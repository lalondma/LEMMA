import openai
import pandas as pd
from duckduckgo_search import DDGS
# from openai.embeddings_utils import get_embedding, cosine_similarity
from openai import OpenAI
import os
import numpy as np
from config import prompts_root

openai.api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI()
with open(prompts_root+'keyword_prompt.md', 'r', encoding='utf-8') as f:
        keyword_prompts = f.read()

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def get_embedding(text, engine="text-embedding-ada-002"):
    return client.embeddings.create(input=[text], model=engine).data[0].embedding


def create_embedding(query):
    return get_embedding(query, engine="text-embedding-ada-002")


def markdown_litteral(string: str):
    return string.replace('$', '\$')


def find_top_similar_results(df: pd.DataFrame, query: str, n: int):
    if len(df.index) < n:
        n = len(df.index)
    embedding = create_embedding(query)
    df1 = df.copy()
    df1["similarities"] = df1["ada_search"].apply(lambda x: cosine_similarity(x, embedding))
    best_results = df1.sort_values("similarities", ascending=False).head(n)
    return best_results.drop(['similarities', 'ada_search'], axis=1).drop_duplicates(subset=['text'])


def ddg_search(query: str):
    with DDGS() as ddgs:
        results=list(ddgs.text('live free or die', region='wt-wt', safesearch='off', timelimit='y', max_results=10))
    # results = ddg(query, region="wt-wt", safesearch="off", max_results=15)
    # query=ddg_translate(query, to = "en")["translated"]
    # results += ddg(query, region="wt-wt", safesearch="off",max_results=10)
    if results == None or results == []:
        print("No search result!")
        return None
    results = pd.DataFrame(results)
    results.columns = ['title', 'link', 'text']
    results['query'] = [query for _ in results.index]
    results['text_length'] = results['text'].str.len()
    results['ada_search'] = results['text'].apply(lambda x: create_embedding(x))
    return results


def make_new_internet_search(keywords, user_query_text):
    search_results = ddg_search(keywords)
    if search_results is None:
        return None
    similar_results = find_top_similar_results(search_results, user_query_text, 4)
    google_findings = similar_results['text'].to_list()
    links = similar_results['link'].to_list()
    return google_findings, links


def display_search_results(google_findings, links):
    res_txt = ""
    for i, finding in enumerate(google_findings):
        res_txt += markdown_litteral(finding) + f' [Source]({links[i]})'
    return res_txt


def generate_keywords(text):
    completion = client.chat.completions.create(
        model="gpt-4-1106-preview",
        # model="gpt-3.5-turbo",
        messages=[
            {"role": "system",
             "content": "You are an professional in optimizing the keywords for search engine"},
            {"role": "user", "content": keyword_prompts + '\n' + text + '\nKeywords Output:\n'}
        ],
        temperature=0.1
    )
    response = completion.choices[0].message.content
    # return response
    keywords = response.replace("\n", " ").split(" ")
    if keywords[0] == "False":
        return "False"
    else:
        return " ".join(keywords[1:])


def search(text):
    keywords = generate_keywords(text)
    if keywords == "False":
        return None
    serach_results = make_new_internet_search(keywords, text)
    if serach_results is None:
        return None
    google_findings, links = serach_results
    return display_search_results(google_findings, links)


if __name__ == '__main__':
    print(search('''A Holocaust denier arrested in a Scottish fishing village after two years on the run has lost an extradition battle.

Vincent Reynouard, 54, from France, was caught in Anstruther, Fife, and was remanded in custody while French authorities launched an extradition bid.

They cited videos where he allegedly denied the existence of gas chambers in concentration camps.

A 70-Year-Old Engineer Designed This Boots For Elderly Women All Over The World
A 70-Year-Old Engineer Designed This Boots For Elderly Women All Over The World
Ad
Dotmalls
He was arrested in November 2022 on a domestic warrant issued by a French court regarding seven videos made between September 2019 and April 2020.

Fullscreen button
His application against extradition was rejected by the Court of Appeal (Picture: UNPIXS)
His application against extradition was rejected by the Court of Appeal (Picture: UNPIXS)
© Provided by Metro'''))
