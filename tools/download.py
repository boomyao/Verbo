from yt_dlp import YoutubeDL
import argparse
import os
def download_audio_only(url, output_dir = None):
    if output_dir is None:
        output_dir = os.path.join(os.getcwd(), url.split("v=")[1])
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output = os.path.join(output_dir, "original.wav")
    if os.path.exists(output):
        return output
    ydl_opts = {
        'format': '139',
        'recode-audio': 'wav',
        'outtmpl': output,
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return output

def download_video(url, output_path):
    output_dir = os.path.dirname(output_path, url.split("v=")[1])
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output = os.path.join(output_dir, "original.mp4")
    ydl_opts = {
        'format': '401',
        'outtmpl': output,
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def get_video_info(url):
    with YoutubeDL() as ydl:
        info_dict = ydl.extract_info(url, download=False)
    return info_dict

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--url", help="The URL of the video to download")
    parser.add_argument("-o", "--output", help="The output file path")
    parser.add_argument("-t", "--type", help="The type of the video to download")
    args = parser.parse_args()
    if args.type == "audio":
        download_audio_only(args.url, args.output)
    elif args.type == "video":
        download_video(args.url, args.output)
    else:
        print("Invalid type")
