import openai
import os
from openai import OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")
from config import prompts_root

client = OpenAI()
prompt_path=prompts_root+'zero_shot.md'
with open(prompt_path, 'r', encoding='utf-8') as f:
        prompt = f.read()

def zero_shot(text, image_text, tool=None, ):
    global prompt
    print('Predicting...')
    completion = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[
            {"role": "system",
             "content": "You are an expert in Misinformation Detection"},
            {"role": "user",
             "content": prompt.format(TEXT=text, IMAGE=image_text)}
        ],
        temperature=0.1,
    )
    predicted_label = int(completion.choices[0].message.content.split('\n')[0].strip())
    return None, None, None, predicted_label, completion.choices[0].message.content
