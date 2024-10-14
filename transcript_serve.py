from flask import Flask, jsonify
from flask_cors import CORS
import os
import json
from transcribe import run_steps
app = Flask(__name__)
CORS(app)

BASE_DIR = "output"

if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR, exist_ok=True)

def get_translated_transcript(video_id):
    output_dir = f"{BASE_DIR}/{video_id}"
    if not os.path.exists(output_dir) or not os.path.exists(f"{output_dir}/translated_paragraphs.jsonl"):
        url = f"https://www.youtube.com/watch?v={video_id}"
        run_steps(url, output_dir)
    paragraphs = []
    with open(f"{output_dir}/translated_paragraphs.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            paragraphs.append(json.loads(line))
    return paragraphs

@app.route('/transcript/<video_id>', methods=['GET'])
def get_transcript(video_id):
    translated_transcript = get_translated_transcript(video_id)
    return jsonify(translated_transcript)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)