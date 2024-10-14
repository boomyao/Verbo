import argparse
import ffmpeg
import os

def segment(input_file, keyframes_file):
    keyframes = []
    base_dir = os.path.dirname(input_file)
    ext = os.path.splitext(input_file)[1]
    with open(keyframes_file, "r") as f:
        for line in f:
            if line.strip():
                hh, mm, ss, ms = line.split(":")
                hh = int(hh)
                mm = int(mm)
                ss = int(ss)
                ms = int(ms)
                keyframes.append(hh * 3600 + mm * 60 + ss + ms / 1000)

    from_time = 0
    for i in range(len(keyframes) + 1):
        start = from_time
        end = keyframes[i] if i < len(keyframes) else None
        output_dir = f"{base_dir}/{i}"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        output_file = f"{output_dir}/source{ext}"
        input_kwargs = {}
        input_kwargs['ss'] = start
        if end:
            input_kwargs['to'] = end
        output_kwargs = {}
        if ext == ".wav":
            output_kwargs['f'] = 'wav'
        else:
            output_kwargs['codec'] = 'copy'
        ffmpeg.input(input_file, **input_kwargs).output(output_file, **output_kwargs).run(overwrite_output=True)
        from_time = end

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", help="The input file to segment")
    parser.add_argument("-k", "--keyframes", help="The keyframes file")
    args = parser.parse_args()
    segment(args.input, args.keyframes)