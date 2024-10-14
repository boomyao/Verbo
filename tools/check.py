import json

def check_aligned_transcription(transcription_path, aligned_transcription_path):
    transcription_segments = {}
    aligned_transcription_segments = {}

    with open(transcription_path, 'r') as f:
        lines = f.readlines()

    for line in lines:
        data = json.loads(line)
        transcription_segments[data['start']] = data

    with open(aligned_transcription_path, 'r') as f:
        lines = f.readlines()

    for line in lines:
        data = json.loads(line)
        aligned_transcription_segments[data['start']] = data

    if len(transcription_segments) != len(aligned_transcription_segments):
        for start in transcription_segments:
            if start not in aligned_transcription_segments:
                print(f"Missing aligned transcription for start: {start}")
                return False

    else:
        print("Aligned transcription is correct.")
        return True
    
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python check.py <transcription_path> <aligned_transcription_path>")
        sys.exit(1)

    transcription_path = sys.argv[1]
    aligned_transcription_path = sys.argv[2]

    check_aligned_transcription(transcription_path, aligned_transcription_path)