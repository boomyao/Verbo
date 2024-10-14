import ffmpeg
import os

def speed_video(video_path, speed_ratio = 1.0, output_path = None):
    base, ext = os.path.splitext(video_path)
    temp_path = f"{base}_temp{ext}" if output_path is None else output_path

    (
        ffmpeg
        .input(video_path)
        .output(
            temp_path,
            vf=f'setpts={1/speed_ratio}*PTS',
            vcodec='h264_nvenc',
            preset='fast',
            an=None,
            threads=0)
        .global_args('-hwaccel', 'cuda')
        .run(overwrite_output=True, quiet=True)
    )

    if output_path is None:
        os.remove(video_path)
        os.rename(temp_path, video_path)

def concat_video(video_paths, output_file):
    temp_path = f'{output_file}_temp.txt'
    with open(temp_path, 'w', encoding='utf-8') as f:
        for file_path in video_paths:
            f.write(f"file '{file_path}'\n")

    (
        ffmpeg
        .input(temp_path, format='concat', safe=0)
        .output(output_file, c='copy')
        .run(overwrite_output=True)
    )

    os.remove(temp_path)
    

def extract_mute_video(input_file, output_file):
    vcodec = 'copy'

    ffmpeg.input(input_file).output(
        output_file,
        vcodec=vcodec,
        an=None
    ).overwrite_output().run(overwrite_output=True, quiet=True)
    
    print(f"视频提取完成,输出文件: {output_file}")

def split_video_by_timestamps(video_file, timestamps, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    for i, segment in enumerate(timestamps):
        start_time = segment['start']
        end_time = segment['end']
        output_file = os.path.join(output_dir, f"{i}.mp4")
        
        (
            ffmpeg
            .input(video_file, ss=start_time, t=end_time-start_time)
            .output(output_file, c='copy')
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True, quiet=True)
        )
    
    print(f"视频切割完成，共生成 {len(timestamps)} 个片段")

import ffmpeg

def video_has_audio(video_path):
    try:
        probe = ffmpeg.probe(video_path)
        audio_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'audio']
        return len(audio_streams) > 0
    except ffmpeg.Error:
        print(f"Error probing file: {video_path}")
        return False