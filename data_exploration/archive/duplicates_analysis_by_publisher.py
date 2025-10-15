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
print("Input shape ", df_articles.shape)

def clean_publisher(publisher):
    return publisher.lower().replace("the ", "").replace("blogs", "").replace("(pennsylvania)", " ").strip(' ')

df_articles["publisher_clean"] = df_articles["publisher"].apply(clean_publisher)
df_articles.reset_index(drop=True, inplace = True)

print("Starting broader near-duplicates (new version).")

import time
import numpy as np

import pandas as pd
import numpy as np
import time

def mark_duplicates(group: pd.DataFrame, threshold: float = 0.8) -> pd.DataFrame:
    """Mark near-duplicates within a publisher group."""
    seen_titles, seen_bodies, seen_indices = [], [], []
    duplicate_flags, duplicate_of_index = [], []

    for idx, row in group.iterrows():
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

    group["near_duplicates_new"] = duplicate_flags
    group["near_duplicates_new_index"] = duplicate_of_index
    return group

group_col = "publisher_clean"
threshold = 0.8

start = time.time()

df_out = (
    df_articles.groupby(group_col, sort=False, group_keys=False)
               .apply(lambda g: mark_duplicates(g.assign(**{group_col: g.name}), threshold), include_groups=False)
)

end = time.time()
print(f"✅ Completed near-duplicate analysis by '{group_col}' in {end - start:.2f} seconds.")



print("Found all duplicates")
print(f"Total execution time: {end - start:.4f} seconds")

df_out.to_pickle("../../data/processed/duplicates_analysis_test.pkl")
