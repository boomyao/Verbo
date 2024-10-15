from tools.download import download_audio_only
import argparse
import json
import os
from tools.translate import translate, align_translated_paragraphs
from tools.download import get_video_info
from tools.transcribe_speaker import transcribe_audio
from tools.transcribe import get_hotwords_from_video_info

def save_paragraphs(paragraphs, path):
  with open(path, "w", encoding="utf-8") as f:
    for paragraph in paragraphs:
      f.write(json.dumps({
        "start": paragraph["lines"][0]["start"],
        "end": paragraph["lines"][-1]["end"],
        "text": paragraph["text"],
        "translated_text": paragraph.get("translated_text", ""),
        "lines": paragraph.get("lines", []),
        "speaker": paragraph.get("speaker", ""),
      }, ensure_ascii=False) + "\n")

def run_steps(yt_url: str, output_dir: str, should_align: bool = False):
  print(f"Downloading audio from {yt_url}")
  original_audio_path = download_audio_only(yt_url, output_dir)

  base_dir = os.path.dirname(original_audio_path)

  print(f"Getting video info from {yt_url}")
  if not os.path.exists(os.path.join(base_dir, "video_info.json")):
    video_info = get_video_info(yt_url)
    hotwords = get_hotwords_from_video_info(video_info)
    video_info["hotwords"] = hotwords
    with open(os.path.join(base_dir, "video_info.json"), "w", encoding="utf-8") as f:
      json.dump(video_info, f, ensure_ascii=False)
  else:
    with open(os.path.join(base_dir, "video_info.json"), encoding="utf-8") as f:
      video_info = json.load(f)
    hotwords = video_info["hotwords"]

  print(f"Transcribing {original_audio_path}")
  transcription_path = os.path.join(base_dir, "transcription.json")
  if not os.path.exists(transcription_path):
    transcribed_segments = transcribe_audio(original_audio_path, hotwords)
    with open(transcription_path, "w", encoding="utf-8") as f:
      json.dump(transcribed_segments, f, ensure_ascii=False)
  else:
    with open(transcription_path, encoding="utf-8") as f:
      transcribed_segments = json.load(f)

  transcription_jsonl_path = os.path.join(base_dir, "transcription.jsonl")
  print(f"Writing transcription to {transcription_jsonl_path}")
  if not os.path.exists(transcription_jsonl_path):
    with open(transcription_jsonl_path, "w", encoding="utf-8") as f:
      for segment in transcribed_segments["segments"]:
        f.write(json.dumps(segment, ensure_ascii=False) + "\n")

  print(f"Translating to paragraphs")
  translated_paragraphs_path = os.path.join(base_dir, "translated_paragraphs.jsonl")
  if not os.path.exists(translated_paragraphs_path):
    translated_paragraphs = translate(transcription_jsonl_path)
    save_paragraphs(translated_paragraphs, translated_paragraphs_path)
  else:
    with open(translated_paragraphs_path, encoding="utf-8") as f:
      translated_paragraphs = [json.loads(line) for line in f.readlines()]

  if should_align:
    print(f"Aligning translated paragraphs")
    aligned_lines = align_translated_paragraphs(translated_paragraphs)
    aligned_map = {}
    for line in aligned_lines:
      aligned_map[line["start"]] = line
    for paragraph in translated_paragraphs:
      for line in paragraph["lines"]:
        line["translated_text"] = aligned_map[line["start"]]["translated_text"]
    save_paragraphs(translated_paragraphs, translated_paragraphs_path)

  print(f"Done")

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--url", type=str, required=True)
  parser.add_argument("-o", "--output_dir", type=str, default=None)
  args = parser.parse_args()

  run_steps(args.url, args.output_dir)
