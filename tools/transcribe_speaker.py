from typing import List
import whisperx
import torch
import os
import logging
import time
logger = logging.getLogger(__name__)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
compute_type = "float16" if torch.cuda.is_available() else "float32"
batch_size = 16

def transcribe_audio(audio_path: str, hotwords: List[str] = []):
  HF_TOKEN = os.environ["HF_TOKEN"]

  if not HF_TOKEN:
    raise ValueError("HF_TOKEN is not set")

  start_time = time.time()
  # transcribe
  model = whisperx.load_model("large-v3", device=DEVICE, compute_type=compute_type, asr_options={"initial_prompt": ','.join(hotwords)})
  audio = whisperx.load_audio(audio_path)
  result = model.transcribe(audio, batch_size=batch_size)
  # model = faster_whisper.WhisperModel("large-v3", device=DEVICE, compute_type=compute_type)
  # segments, info = model.transcribe(audio_path, beam_size=5, hotwords=','.join(hotwords))
  # segments = [{"text": segment.text, "start": segment.start, "end": segment.end} for segment in segments]
  # result = {"segments": segments, "language": info.language}
  end_time = time.time()
  print(f"Transcribed in {end_time - start_time} seconds")

  # align
  model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=DEVICE)
  result = whisperx.align(result["segments"], model_a, metadata, audio, DEVICE, return_char_alignments=False)
  end_time = time.time()
  logger.debug(f"Aligned in {end_time - start_time} seconds")

  # assign speakers
  diarize_model = whisperx.DiarizationPipeline(use_auth_token=HF_TOKEN, device=DEVICE)
  diarize_segments = diarize_model(audio)

  result = whisperx.assign_word_speakers(diarize_segments, result)
  end_time = time.time()
  logger.debug(f"Assigned speakers in {end_time - start_time} seconds")

  return result
