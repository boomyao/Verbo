import json

def split_paragraphs_by_limit(transcription_lines, paragraph_length=1000):
    paragraphs = []
    head = 0
    cursor = 0
    current_text = ""
    while cursor < len(transcription_lines):
        current_text += transcription_lines[cursor]["text"] + " "
        cursor += 1
        if len(current_text) >= paragraph_length:
            paragraphs.append({ "text": current_text, "lines": transcription_lines[head:cursor] })
            current_text = ""
            head = cursor
    if len(current_text) > 0:
        if (len(current_text) < paragraph_length / 2):
            paragraphs[-1]["text"] = paragraphs[-1]["text"] + current_text
            paragraphs[-1]["lines"] = paragraphs[-1]["lines"] + transcription_lines[head:]
        else:
            paragraphs.append({ "text": current_text, "lines": transcription_lines[head:] })

    return paragraphs

def split_paragraphs_by_speaker(transcription_lines):
    paragraphs = []
    current_text = ""
    current_lines = []
    current_speaker = None
    for line in transcription_lines:
        if line["speaker"] != current_speaker:
            paragraphs.append({ "text": current_text, "lines": current_lines })
            current_text = line["text"]
            current_lines = [line]
            current_speaker = line["speaker"]
        else:
            current_text += line["text"] + " "
            current_lines.append(line)
    if len(current_text) > 0:
        paragraphs.append({ "text": current_text, "lines": current_lines })
    return paragraphs

def split_paragraphs(transcription_file=None, transcription_lines=None, paragraph_length=1000, output_file=None):
    if transcription_file is not None and transcription_lines is None:
        raise ValueError("transcription_lines is required when transcription_file is provided")
    elif transcription_lines is None:
        with open(transcription_file, encoding="utf-8") as f:
            transcription_lines = [json.loads(line) for line in f]

    has_multiple_speakers = len(set([line.get("speaker", None) for line in transcription_lines])) > 1

    if has_multiple_speakers:
        paragraphs = split_paragraphs_by_speaker(transcription_lines)
    else:
        paragraphs = split_paragraphs_by_limit(transcription_lines, paragraph_length)

    if output_file is not None:
        with open(output_file, "w", encoding="utf-8") as f:
            for paragraph in paragraphs:
                f.write(json.dumps(paragraph, ensure_ascii=False) + "\n")
        return output_file
    else:
        return paragraphs
