import ffmpeg
import os
import re
from tools.video import concat_video, speed_video, video_has_audio
from tools.audio import concat_audio
from tqdm import tqdm

def merge_video_and_audio(video_path, audio_path, output_path = None):
    if video_has_audio(video_path):
        return video_path
    
    stream = ffmpeg.input(video_path)
    audio = ffmpeg.input(audio_path)

    video_codec = ffmpeg.probe(video_path)['streams'][0]['codec_name']
    audio_codec = ffmpeg.probe(audio_path)['streams'][0]['codec_name']
  
    vcodec = 'copy' if video_codec == 'h264' else 'h264_nvenc'
    acodec = 'copy' if audio_codec == 'aac' else 'aac'

    tmp_output = output_path if output_path else os.path.join(os.path.dirname(video_path), f"temp_{os.path.basename(video_path)}")

    (
        ffmpeg
        .output(stream, audio, tmp_output, vcodec=vcodec, acodec=acodec, strict='experimental')
        .run(overwrite_output=True, quiet=True)
    )

    os.rename(tmp_output, video_path)

    return output_path

# 组装视频和音频片段
def assemble_video_and_audio(video_dir, audio_dir, output_file, end=None):
    video_files = [f for f in os.listdir(video_dir) if re.match(r'^\d+\.mp4$', f)]
    audio_files = [f for f in os.listdir(audio_dir) if re.match(r'^\d+\.wav$', f)]

    count = len(video_files) if end is None else end

    video_files.sort(key=lambda x: int(x.split('.')[0]))
    audio_files.sort(key=lambda x: int(x.split('.')[0]))

    video_speed_dir = f"{os.path.dirname(output_file)}/video_speed"
    os.makedirs(video_speed_dir, exist_ok=True)

    for i in tqdm(range(count)):
        process_video(video_dir, audio_dir, video_speed_dir, i)

    # temp_video_file = f"{video_speed_dir}/_output.mp4"
    # concat_video([f"{i}.mp4" for i in range(count)], temp_video_file)
    # temp_audio_file = f"{audio_dir}/_output.wav"
    # concat_audio([f"{i}.wav" for i in range(count)], temp_audio_file)

    # merge_video_and_audio(temp_video_file, temp_audio_file, output_file)

    for i in tqdm(range(count), desc="merge video and audio"):
        video_file = f"{video_speed_dir}/{i}.mp4"
        audio_file = f"{audio_dir}/{i}.wav"
        merge_video_and_audio(video_file, audio_file)

    concat_video([os.path.abspath(f"{video_speed_dir}/{i}.mp4") for i in range(count)], output_file)

    # os.remove(temp_video_file)
    # os.remove(temp_audio_file)

def process_video(video_dir, audio_dir, video_speed_dir, i):
    video_name = f"{i}.mp4"
    audio_name = f"{i}.wav"
    speed_video_file = f"{video_speed_dir}/{video_name}"
    video_file = f"{video_dir}/{video_name}"
    audio_file = f"{audio_dir}/{audio_name}"
    if not os.path.exists(speed_video_file):
        audio_duration = ffmpeg.probe(audio_file)["format"]["duration"]
        video_duration = ffmpeg.probe(video_file)["format"]["duration"]
        speed_ratio = float(video_duration) / float(audio_duration)
        speed_video(video_file, speed_ratio=speed_ratio, output_path=speed_video_file)
        # merge_video_and_audio(speed_video_file, audio_file)

if __name__ == "__main__":
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument("-v", "--video_dir", type=str, required=True)
  parser.add_argument("-a", "--audio_dir", type=str, required=True)
  parser.add_argument("-o", "--output_file", type=str, required=True)
  parser.add_argument("-e", "--end", type=int, default=None)
  args = parser.parse_args()

  assemble_video_and_audio(args.video_dir, args.audio_dir, args.output_file, args.end)