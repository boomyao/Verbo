from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import json
from transcribe import run_steps
from tools.transcribe import get_transcript_from_youtube
from tools.paragraph import split_paragraphs_by_limit
from tools.translate import direct_translate_text

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

@app.route('/transcript_yt/<video_id>', methods=['GET'])
def get_transcript_yt(video_id):
    transcript = get_transcript_from_youtube(video_id)
    if transcript is None:
        return jsonify({"error": "Failed to fetch transcript from YouTube"}), 500
    
    transcription_lines = [{
        "start": line["start"],
        "end": line["start"] + line["duration"],
        "text": line["text"],
    } for line in transcript]
    paragraphs = split_paragraphs_by_limit(transcription_lines)
    for paragraph in paragraphs:
        paragraph["start"] = paragraph["lines"][0]["start"]
        paragraph["end"] = paragraph["lines"][-1]["end"]

    return paragraphs

@app.route('/translate/direct', methods=['POST'])
def translate_direct():
    data = request.json
    text = data.get("text")
    translated_text = direct_translate_text(text, model="glm-4-flash", base_url=os.getenv("GLM_BASE_URL"), api_key=os.getenv("GLM_API_KEY"))
    return jsonify({"translated_text": translated_text})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)