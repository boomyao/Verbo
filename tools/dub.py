import os
import json
import concurrent.futures
from tqdm import tqdm
import soundfile as sf
import requests
from tools.audio import speed_audio

# from openai import OpenAI
# from openai import OpenAI
# client = OpenAI()
# def dub_audio(tts_text, output_wav):
#     response = client.audio.speech.create(
#       model="tts-1",
#       voice="alloy",
#       input=tts_text
#     )

#     response.write_to_file(output_wav)

def few_shot_tts(tts_text, output_wav, prompt_wav, prompt_text, extra_prompt_wavs = []):
    speed = 0.92
    payload = {
        'text': tts_text,
        'prompt_text': prompt_text,
        'model_id': '6db1cc3f-5797-405d-a98a-f8edfd989c30',
        'ref_id': '1475e092-0033-4f20-bd02-dad6fe79cd93',
        'extra_ref_ids': [
            '0c4f4f3e-befd-4808-82d2-b55fd7c75ad2',
            'f409cb65-6970-4413-bcad-6e97321620d0'
        ],
    }
    # files = [
    #     ('ref_audio', ('ref_audio', open(prompt_wav, 'rb'), 'application/octet-stream')),
    # ]
    # for i, extra_prompt_wav in enumerate(extra_prompt_wavs):
    #     files.append(('ref_audio_{}'.format(i + 2), ('ref_audio_{}'.format(i + 2), open(extra_prompt_wav, 'rb'), 'application/octet-stream')))

    response = requests.post('http://localhost:55001/tts', data=json.dumps(payload), headers={'Content-Type': 'application/json'})

    if response.status_code != 200:
        raise Exception(f"Failed to generate audio: {response.status_code} - {tts_text}")

    with open(output_wav, 'wb') as f:
        f.write(response.content)

    if speed != 1:
        speed_audio(output_wav, speed=speed)

def dub(audio_segments_dir, aligned_transcription_file, output_dir, force=False):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    list_paragraphs = []
    with open(aligned_transcription_file, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            list_paragraphs.append(data)

    orignal_list_paragraphs = []
    with open(os.path.join(os.path.dirname(aligned_transcription_file), "transcription.jsonl"), "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            orignal_list_paragraphs.append(data)

    redub_indexes = []
    for i in range(len(list_paragraphs)):
        if (force):
            redub_indexes.append(i)
        elif not os.path.exists(f"{output_dir}/{i}.wav"):
            redub_indexes.append(i)

    # 创建参数列表
    args_list = [(i, output_dir, force) for i in redub_indexes]

    # 使用线程池并行执行配音任务
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        list(tqdm(
            # executor.map(dub_audio, [list_paragraphs[i]["text"] for i in redub_indexes], [f"{output_dir}/{i}.wav" for i in redub_indexes]), 
            executor.map(few_shot_tts,
                         [list_paragraphs[i]["text"] for i in redub_indexes],
                         [f"{output_dir}/{i}.wav" for i in redub_indexes],
                         [audio_segments_dir + "/{}.wav".format(i) for i in redub_indexes],
                         [orignal_list_paragraphs[i]["text"] for i in redub_indexes],
                         [(audio_segments_dir + "/{}.wav".format(j) for j in range(i, i + 3)) for i in redub_indexes]
                         ), 
            total=len(args_list), 
            desc="配音进度"
        ))

    return redub_indexes

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Dub audio segments")
    parser.add_argument("-i", "--input_dir", type=str, required=True, help="Directory containing audio segments")
    parser.add_argument("-o", "--output_dir", type=str, required=True, help="Output directory for dubbed audio segments")
    parser.add_argument("-a", "--aligned_transcription_file", type=str, required=True, help="Aligned transcription file")
    parser.add_argument("-f", "--force", action="store_true", help="Force overwrite existing files")

    args = parser.parse_args()

    dub(args.input_dir, args.aligned_transcription_file, args.output_dir, args.force)
