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

def align_translated(sentences, translated, max_retry=3):
    sentences_str = ""
    for sentence in sentences:
        sentences_str += json.dumps(sentence, ensure_ascii=False) + "\n"
    client = OpenAI()
    user_content = """
Please align the translated Chinese content with the time-stamped data below based on the meaning of each sentence, following these specific requirements:

Alignment:

Sentence-by-Sentence Comparison: For each English sentence in the timestamps, find the most semantically matching part in the translated Chinese content.
Sentence Splitting or Merging: If the sentence structure in Chinese differs from the English version, appropriately split or merge the Chinese content to match the timestamps.
Ensure Consistent Meaning: Regardless of sentence structure changes, make sure that the Chinese text in each timestamp conveys the same meaning as the corresponding English text.
Replace Text:

Replace the "text" Field: Replace the "text" field in each timestamped data with the corresponding Chinese translation.
Preserve Structure:

Keep "start" and "end" Fields Unchanged: Only replace the content of the "text" field; keep the other fields as they are.
Output Format:

Output in JSON Format:
{{
  "aligned_data": [
    {{"start": number, "end": number, "text": "<chinese_text>"}},
    ...
  ]
}}
Example:
English Timestamp:
{{"start": 0.0, "end": 5.0, "text": "Hello world."}}
Translated Chinese Content:
大家好，这是一个示例。
Aligned Result:
{{
  "aligned_data": [
    {{"start": 0.0, "end": 5.0, "text": "大家好。"}}
  ]
}}

### Translated Chinese Content:
{translated}

### Time-Stamped Data to Align:
{sentences_str}
""".format(sentences_str=sentences_str, translated=translated)
    response = client.chat.completions.create(
        model= 'gpt-4o-mini' if max_retry > 0 else 'gpt-4o',
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
    lines = json_repair.loads(result)["aligned_data"]
    lines = [{"start": line["start"], "end": line["end"], "text": line["text"]} for line in lines if line["text"] != ""]
    if len(lines) != len(sentences):
        if max_retry > 0:
            print("align_translated failed, retry with repair_aligned_translated.")
            print(lines)
            return align_translated(sentences, translated, max_retry - 1)
        else:
            print(user_content)
            print(lines)
            raise Exception("aligned items count not match!\n"
                            "sentences: {}\n"
                            "lines: {}".format(len(sentences), len(lines)))

    return lines

def direct_translate_text(text, model='gpt-4o-mini', base_url=None, api_key=None):
    client = OpenAI(base_url=base_url, api_key=api_key)
    user_content = """
Translate the following input content into Chinese:

## Output

Output in JSON Format:
{{
  "translated_text": "<chinese_text>"
}}

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
        response_format={ "type": "json_object" }
    )
    return json_repair.loads(response.choices[0].message.content)["translated_text"]

def translate_text(text, max_retry=3):
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
        if max_retry > 0:
            logger.error(e, exc_info=True)
            return translate_text(text, max_retry - 1)
        else:
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

def align_translated_paragraphs(translated_paragraphs, output_file=None):
    list_aligned = []
    with tqdm(total=len(translated_paragraphs), desc="Aligning translated paragraphs") as pbar:
        for paragraph in translated_paragraphs:
            aligned = align_translated(paragraph["lines"], paragraph["translated_text"])
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
