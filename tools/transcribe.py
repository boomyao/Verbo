import os
import json
import re
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from faster_whisper import WhisperModel
import torch
from openai import OpenAI

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

def format_transcription(transcription):
    transcription = transcription.strip()
    transcription = re.sub(r'([A-Z]+)-(\d+)', r'\1\2', transcription)
    transcription = re.sub(r'\.\.\.', '', transcription)
    transcription = re.sub(r'\d{1,3}(,\d{2,3})+', lambda x: x.group(0).replace(',', ''), transcription)
    return transcription

def transcribe_audio(model, audio_path, hotwords=[]):
    segments, _ = model.transcribe(audio_path, task="transcribe", hotwords=','.join(hotwords), word_timestamps=True)
    segments = list(segments)
    return segments

def combine_words(segments):
    parts = []
    text = ""
    start = 0
    for segment in segments:
        for word in segment.words:
            text += word.word
            duration = word.end - start
            is_satisfied = duration > 3 and len(text) > 30
            is_too_long = len(text) > 300
            is_dot_ending = text[-1] == "." and text[-2] != "."
            is_nice_condition = is_satisfied and (is_dot_ending or text[-1] == '?' or text[-1] == '!')
            if is_nice_condition or is_too_long:
                parts.append({
                    "start": start,
                    "end": word.end,
                    "text": format_transcription(text)
                })
                start = word.end
                text = ""
    return parts

def transcribe(sliced_audio_dir, output_file):
    model = WhisperModel("large-v3", device=DEVICE)
    audio_files = os.listdir(sliced_audio_dir)
    transcriptions = []
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_audio = {executor.submit(transcribe_audio, model, os.path.join(sliced_audio_dir, audio_file)): audio_file for audio_file in audio_files}
        
        for future in tqdm(as_completed(future_to_audio), total=len(audio_files), desc="转录进度"):
            audio_file = future_to_audio[future]
            try:
                segments = future.result()
                name_parts = audio_file.split("_")
                start_time = int(name_parts[1]) / 32000
                parts = combine_words(segments)
                for part in parts:
                    transcriptions.append({
                        "start": start_time + part["start"],
                        "end": start_time + part["end"],
                        "text": part["text"]
                    })
            except Exception as exc:
                print(f'{audio_file} 转录出错: {exc}')
    
    sorted_transcriptions = sorted(transcriptions, key=lambda x: x["start"])
    with open(output_file, "w") as f:
        for transcription in sorted_transcriptions:
            f.write(json.dumps(transcription, ensure_ascii=False))
            f.write("\n")

def get_hotwords_from_video_info(video_info):
    title = video_info.get("title", "")
    description = video_info.get("description", "")

    if not title and not description:
        return []
    
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    prompt = f"The title of the video is {title}. The description of the video is {description}. Please generate 5-8 hotwords that are likely to appear in the video. Please return a JSON array of strings."
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        response_format={"type": "json_object"}
    )
    hotwords = json.loads(response.choices[0].message.content)
    if not isinstance(hotwords, list):
        hotwords = hotwords.get("hotwords", [])
    return hotwords

if __name__ == "__main__":
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument("-i", "--sliced_audio_dir", type=str, required=True)
  parser.add_argument("-o", "--output_file", type=str, required=True)
  args = parser.parse_args()

  transcribe(args.sliced_audio_dir, args.output_file)