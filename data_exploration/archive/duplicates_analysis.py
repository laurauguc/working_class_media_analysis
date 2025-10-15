import os
import sys
import time
import pandas as pd
import numpy as np


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.getcwd()))))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.getcwd())))))
from data_preparation.utils import standardize_text, add_duplicate_flags, compute_similarity_simple

# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------
#INPUT_PATH = "../../data/processed/parsed_articles.pkl"
#OUTPUT_PATH = "../../data/processed/duplicates_analysis_filter_test.pkl"
#GROUP_COL = "publisher_clean"
#THRESHOLD = 0.8

# ---------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------
#df_articles = pd.read_pickle(INPUT_PATH).head(1000)
#print(f"✅ Loaded data: {df_articles.shape[0]} rows, {df_articles.shape[1]} columns")

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def clean_publisher(publisher: str) -> str:
    """Standardize publisher names by removing common variations."""
    return (
        publisher.lower()
        .replace("the ", "")
        .replace("blogs", "")
        .replace("(pennsylvania)", " ")
        .strip()
    )

def mark_duplicates(group: pd.DataFrame, threshold: float = 0.8) -> pd.DataFrame:
    """
    Identify near-duplicates within a publisher group based on title and body similarity.
    Marks duplicates and references the index of the original article.
    """
    seen_titles, seen_bodies, seen_indices = [], [], []
    duplicate_flags, duplicate_of_index = [], []

    for idx, row in group.iterrows():
        title, body = row["title"], row["body"]
        is_duplicate, duplicate_index = False, np.nan

        for seen_title, seen_body, seen_idx in zip(seen_titles, seen_bodies, seen_indices):
            if compute_similarity_simple(title, seen_title) < 0.5:
                continue
            if compute_similarity_simple(body, seen_body) >= threshold:
                is_duplicate, duplicate_index = True, seen_idx
                break

        duplicate_flags.append(is_duplicate)
        duplicate_of_index.append(duplicate_index)

        if not is_duplicate:
            seen_titles.append(title)
            seen_bodies.append(body)
            seen_indices.append(idx)

    group["near_duplicate"] = duplicate_flags
    group["near_duplicate_index"] = duplicate_of_index
    return group


# ---------------------------------------------------------------------
# Preprocessing
# ---------------------------------------------------------------------

def find_near_duplicates(df_articles, threshold, group_col):
    df_articles["publisher_clean"] = df_articles["publisher"].apply(clean_publisher)
    df_articles.reset_index(drop=True, inplace=True)
    # Duplicate Detection
    df_out = (
        df_articles.groupby(group_col, sort=False, group_keys=False)
        .apply(lambda g: mark_duplicates(g, threshold))
    )

    near_dup_mask = df_out["near_duplicate"]]
    return return near_dup_mask
