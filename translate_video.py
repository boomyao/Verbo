import os
import json
import argparse
import re
from tools.audio import extract_audio_from_video, slice_audio_rms, split_audio_by_timestamps
from tools.video import extract_mute_video, split_video_by_timestamps
from tools.media import assemble_video_and_audio
from tools.dub import dub
from tools.transcribe import transcribe
from tools.translate import translate, align_translated_paragraphs
from tools.subtitle import generate_subtitle

def run_steps(input, output):
    os.makedirs(output, exist_ok=True)

    print("Extracting audio from video...")
    if not os.path.exists(f"{output}/source.wav"):
        extract_audio_from_video(input, f"{output}/source.wav")

    print("Splitting audio...")
    if not os.path.exists(f"{output}/sliced_audio"):
        slice_audio_rms(f"{output}/source.wav", f"{output}/sliced_audio")

    print("Transcribing audio...")
    if not os.path.exists(f"{output}/transcription.jsonl"):
        transcribe(f"{output}/sliced_audio", f"{output}/transcription.jsonl")

    print("Aligning and translating transcription...")
    if not os.path.exists(f"{output}/aligned_transcription.jsonl"):
        paragraphs = translate(f"{output}/transcription.jsonl")
        align_translated_paragraphs(paragraphs, output_file=f"{output}/aligned_transcription.jsonl")

    timestamps = []
    with open(f"{output}/aligned_transcription.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            timestamps.append({
                "start": item["start"],
                "end": item["end"],
            })

    print("Splitting audio...")
    if not os.path.exists(f"{output}/splitted_audio"):
        split_audio_by_timestamps(f"{output}/source.wav", timestamps, f"{output}/splitted_audio")

    print("Extracting video...")
    if not os.path.exists(f"{output}/source.mp4"): 
        extract_mute_video(input, f"{output}/source.mp4")

    print("Splitting video...")
    if not os.path.exists(f"{output}/splitted_video"):
        split_video_by_timestamps(f"{output}/source.mp4", timestamps, f"{output}/splitted_video")

    print("DUBbing audio...")
    redub_indexes = dub(f"{output}/splitted_audio", f"{output}/aligned_transcription.jsonl", f"{output}/dubbed_audio")

    print("Assembling video and audio...")
    if not os.path.exists(f"{output}/output.mp4") or len(redub_indexes) > 0:
        assemble_video_and_audio(f"{output}/splitted_video", f"{output}/dubbed_audio", f"{output}/output.mp4")

    print("Generating subtitle...")
    if not os.path.exists(f"{output}/subtitle.srt") or len(redub_indexes) > 0:
        generate_subtitle(f"{output}/aligned_transcription.jsonl", f"{output}/subtitle.srt", dubbed_dir=f"{output}/dubbed_audio")

def optimize_filename(filename):
    return re.sub(r"[ ()（）/:.,']+", '_', filename)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", type=str, required=True, help="Input video file or directory")
    parser.add_argument("-o", "--output", type=str, required=True, help="Output directory")
    args = parser.parse_args()

    # if args.input is a directory, process all videos in the directory
    if os.path.isdir(args.input):
        for file in os.listdir(args.input):
            if file.endswith(".mp4"):
                input = os.path.join(args.input, file)
                output = os.path.join(args.output, optimize_filename(file))
                if os.path.exists(output):
                    print(f"Skipping {output} because it already exists")
                    continue
                run_steps(input, output)
    else:
        run_steps(args.input, args.output)