import os
import requests
import torch
import torchaudio
import soundfile as sf
import numpy as np

ZH_BASE_TTS_TEXTS = [
  "量子计算机通过利用量子叠加和量子纠缠的特性，能够在极短的时间内处理传统计算机无法解决的复杂问题。",
  "随着深度学习和神经网络技术的飞速进步，人工智能在图像识别、自然语言处理和自动驾驶等领域取得了显著成果。"
]

def zero_shot_tts(tts_text, prompt_wav, output_wav):
    payload = {
        'tts_text': tts_text
    }
    
    audio, sample_rate = sf.read(prompt_wav)
    
    # 如果音频长度超过30秒,裁剪前30秒
    max_duration = 30  # 最大持续时间(秒)
    max_samples = max_duration * sample_rate
    
    temp_wav = None
    if len(audio) > max_samples:
        audio = audio[:max_samples]
        
        # 创建临时文件保存裁剪后的音频
        temp_wav = f'temp_{os.path.basename(prompt_wav)}'
        sf.write(temp_wav, audio, sample_rate)
        prompt_wav = temp_wav

    files = [('prompt_wav', ('prompt_wav', open(prompt_wav, 'rb'), 'application/octet-stream'))]
    response = requests.get('http://localhost:50000/inference_cross_lingual', data=payload, files=files)
    
    # 如果创建了临时文件,删除它
    if temp_wav and os.path.exists(temp_wav):
        os.remove(temp_wav)
    
    tts_audio = b''
    for r in response.iter_content(chunk_size=16000):
        tts_audio += r
    tts_speech = torch.from_numpy(np.array(np.frombuffer(tts_audio, dtype=np.int16))).unsqueeze(dim=0)
    torchaudio.save(output_wav, tts_speech, 22050)

def dub_voice_prompt(prompt_wav, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    for i in range(len(ZH_BASE_TTS_TEXTS)):
        zero_shot_tts(ZH_BASE_TTS_TEXTS[i], prompt_wav, f"{output_dir}/prompt_{i + 1}.wav")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--prompt_wav", type=str, required=True)
    parser.add_argument("-o", "--output_dir", type=str, required=True)
    args = parser.parse_args()
    dub_voice_prompt(args.prompt_wav, args.output_dir)
