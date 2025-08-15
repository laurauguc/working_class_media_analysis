import re
import calendar

def standardize_text(text, title_stop_words = None):
    # Remove all non-alphanumeric characters except spaces
    clean_text = re.sub(r'[^a-zA-Z0-9 ]', '', text.strip()).lower()

    if title_stop_words:
        # Remove stop words
        words = clean_text.split()
        filtered_words = [w for w in words if w not in title_stop_words]
        return " ".join(filtered_words)

    return(clean_text)

import re

def compute_similarity_simple(text1: str, text2: str) -> float:
    """
    Compute a simple word-overlap similarity score between two texts.
    Uses Jaccard similarity (intersection over union of unique words).

    Args:
        text1 (str): The first article or document.
        text2 (str): The second article or document.

    Returns:
        float: Similarity score between 0 and 1.
    """
    # Convert to lowercase, remove non-alphanumeric, split into words
    tokenize = lambda text: set(re.findall(r'\b\w+\b', text.lower()))

    words1 = tokenize(text1)
    words2 = tokenize(text2)

    if not words1 or not words2:
        return 0.0  # Avoid division by zero

    overlap = len(words1 & words2)
    union = len(words1 | words2)

    return overlap / union

def obtain_similarity_dictionary(titles, threshold):
    similar_dict = {}  # start empty
    n = len(titles)
    for i in range(n):
        for j in range(i + 1, len(titles)):  # skip repeats
            score = compute_similarity_simple (titles[i], titles[j])
            if score > threshold:
                similar_dict.setdefault(titles[i], []).append((titles[j], score))
                similar_dict.setdefault(titles[j], []).append((titles[i], score))
    return(similar_dict)


def create_date_components():
    # Months: lowercase
    months = [month.lower() for month in list(calendar.month_name)[1:]]

    # Days: zero-padded 01–31
    days = [f"{day:02}" for day in range(4, 31)]
    days = ['01st', '02nd', '03rd'] + [i+'th' for i in days] + ['31st']

    # Weekdays: lowercase
    weekdays = [day.lower() for day in list(calendar.day_name)]

    # Years: 1980–2025
    years = [str(i) for i in range(1980, 2026)]

    return months +  days + weekdays + years

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import numpy as np


def compute_similarity(text1: str, text2: str) -> float:
    """
    Compute the similarity score between two texts using TF-IDF and cosine similarity.
    """
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform([text1, text2])
    similarity_matrix = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
    return similarity_matrix[0][0]


def mark_duplicates(group, threshold):
    """
    Mark duplicates within a group based on the given similarity threshold.
    Also records the index of the first matching duplicate.
    """
    seen_bodies = []
    seen_indices = []
    duplicate_flags = []
    duplicate_of_index = []

    for idx, row in group.iterrows():
        body = row['body']
        is_duplicate = False
        duplicate_index = np.nan

        for seen_body, seen_idx in zip(seen_bodies, seen_indices):
            similarity = compute_similarity(body, seen_body)
            if similarity >= threshold:
                is_duplicate = True
                duplicate_index = seen_idx
                break

        duplicate_flags.append(is_duplicate)
        duplicate_of_index.append(duplicate_index)

        if not is_duplicate:
            seen_bodies.append(body)
            seen_indices.append(idx)

    flag_col = f"is_near_duplicate_{int(threshold*100)}"
    idx_col = f"duplicate_of_index_{int(threshold*100)}"
    group[flag_col] = duplicate_flags
    group[idx_col] = duplicate_of_index
    return group


def add_duplicate_flags(df, group_col, thresholds):
    """
    Adds duplicate flags and duplicate-of index columns for each threshold.
    """
    df_out = df.copy()
    for t in thresholds:
        print(f"Obtaining near-duplicates flag for {t} threshold")


        df_out = (
            df_out.groupby(group_col, sort=False, group_keys=False)
                  .apply(lambda g: mark_duplicates(g.assign(**{group_col: g.name}), t), include_groups=False)
        )

        # return the title to the beginning
        #cols = ['title'] + [col for col in df_out.columns if col != 'title']
        #df_out = df_out[cols]
    return df_out
