import json, logging
import concurrent.futures
from tqdm import tqdm
from tools.paragraph import split_paragraphs
from tools.agent import agentQuickTranslator, agentSentenceAligner, agentTranslator
logger = logging.getLogger(__name__)

def get_transcription_lines(transcription_file, start_line=0, end_line=None):
    with open(transcription_file, "r", encoding="utf-8") as f:
        transcription = f.readlines()
    transcription = [line for line in transcription if len(line.strip()) > 0]
    if end_line is None:
        return [json.loads(line) for line in transcription[start_line:]]
    else:
        return [json.loads(line) for line in transcription[start_line:end_line]]

def align_translated(sentences, translated):
    aligned_sentences = agentSentenceAligner(sentences, translated)
    
    for i in range(len(sentences)):
        sentences[i]["translated_text"] = aligned_sentences[i]["chinese"]
    return sentences

def translate_text(text):
    if len(text) < 20:
        return agentQuickTranslator(text)
    else:
        return agentTranslator(text)

def translate(transcription_file, paragraph_length=1000, output_file=None, max_workers=10):
    transcription_lines = get_transcription_lines(transcription_file)
    paragraphs = split_paragraphs(transcription_file, transcription_lines, paragraph_length)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for i, paragraph in enumerate(paragraphs):
            future = executor.submit(translate_text, paragraph["text"])
            future.paragraph_index = i
            futures.append(future)
        
        with tqdm(total=len(paragraphs), desc="Translating paragraphs") as pbar:
            for future in concurrent.futures.as_completed(futures):
                i = future.paragraph_index
                try:
                    translated_text = future.result()
                    paragraphs[i]["translated_text"] = translated_text
                except Exception as e:
                    logger.error(f"Translating paragraph {i} failed: {str(e)}")
                finally:
                    pbar.update(1)

    if output_file is not None:
        with open(output_file, "w", encoding="utf-8") as f:
            for paragraph in paragraphs:
                f.write(json.dumps(paragraph, ensure_ascii=False))
                f.write("\n")
        return output_file
    else:
        return paragraphs

def align_translated_paragraphs(translated_paragraphs, output_file=None, max_workers=10):
    list_aligned = []
    
    def process_paragraph(paragraph):
        if len(paragraph["lines"]) == 0:
            return []
        elif len(paragraph["lines"]) == 1:
            paragraph["lines"][0]["translated_text"] = paragraph["translated_text"]
            return paragraph["lines"]
        else:
            return align_translated(paragraph["lines"], paragraph["translated_text"])
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_paragraph, paragraph) for paragraph in translated_paragraphs]
        
        with tqdm(total=len(translated_paragraphs), desc="Aligning translated paragraphs") as pbar:
            for future in concurrent.futures.as_completed(futures):
                aligned = future.result()
                for line in aligned:
                    list_aligned.append(line)
                pbar.update(1)

    list_aligned.sort(key=lambda x: x["start"])
    
    if output_file is not None:
        with open(output_file, "w", encoding="utf-8") as f:
            for aligned in list_aligned:
                f.write(json.dumps(aligned, ensure_ascii=False))
                f.write("\n")
        return output_file
    else:
        return list_aligned
    
def translate_and_align(transcription_file, output_file, paragraph_length=1000):
    paragraphs = translate(transcription_file, output_file, paragraph_length)
    return align_translated_paragraphs(paragraphs, output_file)

if __name__ == "__main__":
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument("-t", "--transcription_file", type=str, required=True)
  parser.add_argument("-o", "--output_file", type=str, required=True)
  args = parser.parse_args()

  translate(args.transcription_file, args.output_file)
