import json
import re
import os
import ffmpeg

def format_time(seconds_time):
    hours = int(seconds_time // 3600)
    minutes = int((seconds_time % 3600) // 60)
    seconds = int(seconds_time % 60)
    milliseconds = int((seconds_time % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def generate_subtitle(aligned_file, output_file, dubbed_dir = None):
    paragraphs = []
    with open(aligned_file, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            paragraphs.append(data)

    if dubbed_dir is not None:
        current_time = 0
        for i in range(len(paragraphs)):
            dubbed_file = os.path.join(dubbed_dir, f"{i}.wav")
            if not os.path.exists(dubbed_file):
                continue
            duration = ffmpeg.probe(dubbed_file)["format"]["duration"]
            paragraphs[i]["start"] = current_time
            current_time += float(duration)
            paragraphs[i]["end"] = current_time

    srt_content = ""
    for paragraph in paragraphs:
        pure_words = re.sub(r'[，。！？]', '', paragraph["text"])
        duration_per_word = (paragraph["end"] - paragraph["start"]) / len(pure_words)
        parts = re.split(r'[，。！？]', paragraph["text"])
        for part in parts:
            if part.strip() == "":
                continue
            srt_content += f"{format_time(paragraph['start'])} --> {format_time(paragraph['start'] + duration_per_word * len(part))}\n"
            srt_content += f"{part}\n\n"
            paragraph['start'] += duration_per_word * len(part)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(srt_content)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--aligned_file", type=str, required=True)
    parser.add_argument("-o", "--output_file", type=str, required=True)
    parser.add_argument("-d", "--dubbed_dir", type=str, required=False)
    args = parser.parse_args()
    generate_subtitle(args.aligned_file, args.output_file, args.dubbed_dir)