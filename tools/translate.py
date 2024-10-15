import os, json, logging
from openai import OpenAI
import json_repair
import concurrent.futures
from tqdm import tqdm
from tools.paragraph import split_paragraphs

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
    sentences_str = ""
    for sentence in sentences:
        sentences_str += '"{}"\n'.format(sentence["text"])
    client = OpenAI()
    user_content = """
Task: Please align the translated Chinese content with the following English sentences based on sentence order, following these specific requirements:

Alignment:

Sentence Order Matching: Match each English sentence with the corresponding Chinese sentence in order.
Sentence Splitting or Merging: If the Chinese sentence structure differs from the English, appropriately split or merge the Chinese content to match the number of English sentences.
Ensure Consistent Meaning: Regardless of structural changes, ensure that each Chinese sentence conveys the same meaning as the corresponding English sentence.
Output Format:

JSON Format:
{{
  "aligned_sentences": [
    {{"english": "<English sentence>", "chinese": "<Chinese translation>"}},
    ...
  ]
}}
Example:

English Sentences:

"Hello world."
"This is a sample."
Translated Chinese Content:

"大家好，这是一个示例。"

Aligned Result:
{{
  "aligned_sentences": [
    {{"english": "Hello world.", "chinese": "大家好。"}},
    {{"english": "This is a sample.", "chinese": "这是一个示例。"}}
  ]
}}
Translated Chinese Content:

{translated}

English Sentences to Align:

{sentences_str}
""".format(sentences_str=sentences_str, translated=translated)
    response = client.chat.completions.create(
        model= 'gpt-4o-mini',
        messages=[
            {"role": "system", "content": 'You are a helpful assistant.'},
            {"role": "user", "content": user_content}
        ],
        max_tokens=2048,
        temperature=0.3,
        top_p=1,
        response_format={ "type": "json_object" }
    )
    result = response.choices[0].message.content
    aligned_sentences = json_repair.loads(result)["aligned_sentences"]
    if len(aligned_sentences) != len(sentences):
        # repair aligned_sentences
        repaired_aligned_sentences = []
        aligned_index = 0
        
        for i, sentence in enumerate(sentences):
            if aligned_index < len(aligned_sentences) and aligned_sentences[aligned_index]["english"].strip() == sentence["text"].strip():
                repaired_aligned_sentences.append(aligned_sentences[aligned_index])
                aligned_index += 1
            else:
                direct_translation = direct_translate_text(sentence["text"])
                repaired_aligned_sentences.append({
                    "english": sentence["text"],
                    "chinese": direct_translation
                })
        
        aligned_sentences = repaired_aligned_sentences
    
    for i in range(len(sentences)):
        sentences[i]["translated_text"] = aligned_sentences[i]["chinese"]
    return sentences

def direct_translate_text(text, model='gpt-4o-mini', base_url=None, api_key=None):
    client = OpenAI(base_url=base_url, api_key=api_key)
    user_content = """
You are a translation assistant. Translate the Input Content into Chinese and output it in the <translation> tag.

## Output

<translation>
[Insert your translation here]
</translation>

## Input Content
{text}
""".format(text=text)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": 'You are a helpful assistant.'},
            {"role": "user", "content": user_content}
        ],
        max_tokens=4095,
        temperature=1,
        top_p=0.7,
    )
    result = response.choices[0].message.content
    if result.startswith("<translation>"):
        result = result.split("<translation>")[1].split("</translation>")[0]
    if result.startswith("\n"):
        result = result[1:]
    return result

def translate_text(text):
    if len(text) < 20:
        return direct_translate_text(text)
    client = OpenAI(api_key=os.getenv("GLM_API_KEY"), base_url=os.getenv("GLM_BASE_URL"))
    user_content = """
You will follow a three-step translation process:
1. Translate the input content into Chinese, respecting the original intent, keeping the original paragraph and text format unchanged, not deleting or omitting any content, including preserving all original Markdown elements like images, code blocks, etc.
2. Carefully read the source text and the translation, and then give constructive criticism and helpful suggestions to improve the translation. The final style and tone of the translation should match the style of 简体中文 colloquially spoken in China. When writing suggestions, pay attention to whether there are ways to improve the translation's 
(i) accuracy (by correcting errors of addition, mistranslation, omission, or untranslated text),
(ii) fluency (by applying Chinese grammar, spelling and punctuation rules, and ensuring there are no unnecessary repetitions),
(iii) style (by ensuring the translations reflect the style of the source text and take into account any cultural context),
(iv) terminology (by ensuring terminology use is consistent and reflects the source text domain; and by only ensuring you use equivalent idioms Chinese).
3. Based on the results of steps 1 and 2, refine and polish the translation

## Glossary

Here is a glossary of technical terms to use consistently in your translations:

- AGI -> 通用人工智能
- LLM/Large Language Model -> 大语言模型
- Transformer -> Transformer
- Token -> Token
- Generative AI -> 生成式 AI
- AI Agent -> AI 智能体
- prompt -> 提示词
- zero-shot -> 零样本学习
- few-shot -> 少样本学习
- multi-modal -> 多模态
- fine-tuning -> 微调


## Output

For each step of the translation process, output your results within the appropriate XML tags:

<step1_initial_translation>
[Insert your initial translation here]
</step1_initial_translation>

<step2_reflection>
[Insert your reflection on the translation, write a list of specific, helpful and constructive suggestions for improving the translation. Each suggestion should address one specific part of the translation.]
</step2_reflection>

<step3_refined_translation>
[Insert your refined and polished translation here]
</step3_refined_translation>

Remember to consistently use the provided glossary for technical terms throughout your translation. Ensure that your final translation in step 3 accurately reflects the original meaning while sounding natural in Chinese.

## Input Content
{text}
""".format(text=text)
    response = client.chat.completions.create(
        model='glm-4-plus',
        messages=[
            {"role": "system", "content": 'You are a helpful assistant.'},
            {"role": "user", "content": user_content}
        ],
        max_tokens=4095,
        temperature=1,
        top_p=0.7,
    )
    try:
        result = response.choices[0].message.content
        result = result.split("<step3_refined_translation>")[1].split("</step3_refined_translation>")[0]
        if result.startswith("\n"):
            result = result[1:]
        return result
    except Exception as e:
        logger.error(user_content)
        logger.error(result)
        raise e

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
