from flask import Flask, jsonify
from flask_cors import CORS
import os
import json
app = Flask(__name__)
CORS(app)

def get_translated_transcript(video_id):
    output_dir = f"outputs/{video_id}"
    if not os.path.exists(output_dir):
        return None
    paragraphs = []
    with open(f"{output_dir}/translated_paragraphs.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            paragraphs.append(json.loads(line, encoding="utf-8"))
    return paragraphs

@app.route('/transcript/<video_id>', methods=['GET'])
def get_transcript(video_id):
    translated_transcript = get_translated_transcript(video_id)
    return jsonify(translated_transcript)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)