import sys
import os
import pandas as pd
from collections import Counter
import matplotlib.pyplot as plt
import json
import numpy as np
import time
import re
from ftfy import fix_text
import pickle


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.getcwd()))))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.getcwd())))))
from data_preparation.utils import standardize_text, add_duplicate_flags, compute_similarity_simple

input_path = "../../data/processed/parsed_articles.pkl"

# Load data
df_articles = pd.read_pickle(input_path)


# Load title stop words
with open("../../data_preparation/title_stop_words.json", "rb") as f:
    title_stop_words = json.load(f)

def clean_text(text):
    text = text.replace(u'\xa0', u' ')
    return fix_text(text).strip(" \n")

def remove_load_date(text: str) -> str:
    """
    Remove 'Load-Date: <Month day, year>' if present at the end of the text.
    """
    # Regex: match optional whitespace, then 'Load-Date:', then date, till the very end
    pattern = r'\s*Load-Date:\s+[A-Za-z]+\s+\d{1,2},\s+\d{4}\s*$'
    return re.sub(pattern, '', text)

# Clean text columns
txt_cols = ['title', 'body']
for txt_col in txt_cols:
    df_articles[txt_col] = df_articles[txt_col].apply(clean_text)

# Standardize titles
df_articles['title_stand'] = df_articles['title'].apply(lambda x: standardize_text(x, title_stop_words))

# Remove trailing load date
df_articles['body'] = df_articles['body'].apply(remove_load_date)

df_articles = df_articles.loc[df_articles['body'] != ""]
df_articles = df_articles.reset_index(drop=True)

# Identify exact duplicates (those that will be dropped)
df_articles['exact_duplicate'] = df_articles.duplicated(subset=["body", "title"], keep='first')
print("Found exact duplicates.")


thresholds = [0.90]
df_articles = add_duplicate_flags(df_articles, "title_stand", thresholds)
df_articles.rename(columns={'is_near_duplicate_90': 'near_duplicate_matching_title'}, inplace=True)
print("Found near-duplicates with matching titles")

print("Starting broader near-duplicates (new version).")

import time
import numpy as np

start = time.time()
start0 = start

threshold = 0.80

seen_bodies = []
seen_indices = []
duplicate_flags = []
duplicate_of_index = []

total = len(df_articles)

seen_titles, seen_bodies, seen_indices = [], [], []
duplicate_flags, duplicate_of_index = [], []

for idx, row in df_articles.iterrows():
    title, body = row["title"], row["body"]

    duplicate_index = np.nan
    is_duplicate = False

    for seen_title, seen_body, seen_idx in zip(seen_titles, seen_bodies, seen_indices):
        if compute_similarity_simple(title, seen_title) < 0.5:
            continue
        if compute_similarity_simple(body, seen_body) >= threshold:
            is_duplicate = True
            duplicate_index = seen_idx
            break

    duplicate_flags.append(is_duplicate)
    duplicate_of_index.append(duplicate_index)

    if not is_duplicate:
        seen_titles.append(title)
        seen_bodies.append(body)
        seen_indices.append(idx)

    if idx % max(1, len(df_articles)//20) == 0:
        end = time.time()
        percent_done = (idx / total) * 100
        print(f"Progress: {percent_done:.1f}%. Execution time: {end - start:.4f} seconds")
        start = time.time()

df_articles["near_duplicates_new"] = duplicate_flags
df_articles["near_duplicates_new_index"] = duplicate_of_index

end = time.time()

print("Found all duplicates")
print(f"Total execution time: {end - start0:.4f} seconds")

df_articles.to_pickle("../../data/processed/duplicates_analysis_80.pkl")
