import ffmpeg
import os
import numpy as np

def concat_audio(audio_paths, output_file):
    temp_path = f'{output_file}_temp.txt'
    with open(temp_path, 'w') as f:
        for file_path in audio_paths:
            f.write(f"file '{file_path}'\n")

    (
        ffmpeg
        .input(temp_path, format='concat', safe=0)
        .output(output_file)
        .run(overwrite_output=True)
    )

    os.remove(temp_path)

def extract_audio_from_video(video_path, output_path):
    (
        ffmpeg
        .input(video_path)
        .output(output_path)
        .run(overwrite_output=True)
    )

def slice_audio_rms(audio_file, output_dir, min_length=60000):
    from tools.slice_audio import slice
    slice(audio_file, output_dir, threshold=-34, min_length=min_length, min_interval=300, hop_size=10, max_sil_kept=500, _max=0.9, alpha=0.25, i_part=0, all_part=1)

def split_audio_by_timestamps(audio_file, timestamps, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    for i, segment in enumerate(timestamps):
        start_time = segment['start']
        end_time = segment['end']
        output_file = os.path.join(output_dir, f"{i}.wav")
        
        (
            ffmpeg
            .input(audio_file, ss=start_time, t=end_time-start_time)
            .output(output_file)
            .run(capture_stdout=True, capture_stderr=True)
        )
    
    print(f"音频切割完成，共生成 {len(timestamps)} 个片段")

def load_audio_with_f32le(file, sr):
    try:
        if os.path.exists(file) == False:
            raise RuntimeError(
                "You input a wrong audio path that does not exists, please fix it!"
            )
        out, _ = (
            ffmpeg.input(file, threads=0)
            .output("-", format="f32le", acodec="pcm_f32le", ac=1, ar=sr)
            .run(cmd=["ffmpeg", "-nostdin"], capture_stdout=True, capture_stderr=True)
        )
    except Exception as e:
        print(e)

    return np.frombuffer(out, np.float32).flatten()

def speed_audio(audio_file, speed, output_file = None):
    if output_file:
        ffmpeg.input(audio_file).output(output_file, af="atempo={}".format(speed)).run(overwrite_output=True, quiet=True)
    else:
        temp_file = f"{audio_file}_temp.wav"
        ffmpeg.input(audio_file).output(temp_file, af="atempo={}".format(speed)).run(overwrite_output=True, quiet=True)
        os.rename(temp_file, audio_file)