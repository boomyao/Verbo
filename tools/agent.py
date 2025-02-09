from openai import OpenAI
import json_repair
import os

ALI_API_KEY = os.getenv("ALI_API_KEY")
ALI_BASE_URL = os.getenv("ALI_BASE_URL")

def agentTranslator(text):
    client = OpenAI(api_key=ALI_API_KEY, base_url=ALI_BASE_URL)
    user_content = """
用中文表达以下内容(最后只需要返回中文内容，不要返回任何解释)：

{text}
""".format(text=text)
    response = client.chat.completions.create(
        model="deepseek-r1-distill-qwen-32b",
        messages=[{"role": "user", "content": user_content}],
        temperature=0.6,
    )
    result = response.choices[0].message.content
    return result
def agentQuickTranslator(text):
    client = OpenAI()
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
        model='gpt-4o-mini',
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

def agentSentenceAligner(sentences, translated):
    sentences_str = ""
    for sentence in sentences:
        sentences_str += '"{}"\n'.format(sentence["text"])
    client = OpenAI(api_key=ALI_API_KEY, base_url=ALI_BASE_URL)
    user_content = """
Please align the translated Chinese content with the following English sentences based on sentence order, make sure the count of aligned sentences is the same as the count of English sentences.

JSON Format:
{{
  "aligned_sentences": [
    {{"english": "<English sentence>", "chinese": "<Chinese translation>"}},
    ...
  ]
}}

Translated Chinese Content:

{translated}

English Sentences to Align:

{sentences_str}
""".format(sentences_str=sentences_str, translated=translated)
    response = client.chat.completions.create(
        model="deepseek-r1-distill-qwen-32b",
        messages=[{"role": "user", "content": user_content}],
        temperature=0.3,
    )
    response_content = response.choices[0].message.content
    try:
        result = json_repair.loads(response_content)["aligned_sentences"]
        if len(result) != len(sentences):
            print(response_content)
            raise Exception("The count of aligned sentences is not the same as the count of English sentences.")
    except Exception as e:
        raise e
    return result

