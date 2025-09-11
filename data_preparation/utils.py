import re
import calendar
import pandas as pd
import pycountry
import re

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


# --- US states with abbreviations ---
US_STATES = {
    "Alabama": "AL","Alaska": "AK","Arizona": "AZ","Arkansas": "AR","California": "CA",
    "Colorado": "CO","Connecticut": "CT","Delaware": "DE","Florida": "FL","Georgia": "GA",
    "Hawaii": "HI","Idaho": "ID","Illinois": "IL","Indiana": "IN","Iowa": "IA","Kansas": "KS",
    "Kentucky": "KY","Louisiana": "LA","Maine": "ME","Maryland": "MD","Massachusetts": "MA",
    "Michigan": "MI","Minnesota": "MN","Mississippi": "MS","Missouri": "MO","Montana": "MT",
    "Nebraska": "NE","Nevada": "NV","New Hampshire": "NH","New Jersey": "NJ","New Mexico": "NM",
    "New York": "NY","North Carolina": "NC","North Dakota": "ND","Ohio": "OH","Oklahoma": "OK",
    "Oregon": "OR","Pennsylvania": "PA","Rhode Island": "RI","South Carolina": "SC","South Dakota": "SD",
    "Tennessee": "TN","Texas": "TX","Utah": "UT","Vermont": "VT","Virginia": "VA","Washington": "WA",
    "West Virginia": "WV","Wisconsin": "WI","Wyoming": "WY"
}

# --- US regions (only unambiguous ones) ---
US_REGIONS = ["Midwest", "Pacific Northwest", "New England"]

# --- Other US indicators ---
US_INDICATORS = ["USA", "US", "U.S.", "United States", "America"]

# --- Alternative names for foreign countries ---
ALT_NAMES = {
    "United Kingdom": ["UK", "Britain", "England"],
    "Russia": ["Russian Federation"],
    "South Korea": ["Republic of Korea"],
    "North Korea": ["Democratic People's Republic of Korea"],
    "Iran": ["Iran, Islamic Republic of"],
    "Syria": ["Syrian Arab Republic"],
    "Venezuela": ["Bolivarian Republic of Venezuela"]
}

# --- Function to safely detect US state abbreviations in parentheses or after comma+space ---
def match_state_abbr(text, state, abbr):
    # Match "(CA)" or ", CA"
    pattern = rf"(?:\(\s*{re.escape(abbr)}\s*\)|,\s*{re.escape(abbr)})"
    return re.search(pattern, text)

# --- Function to check countries/flags in text ---
def find_country_flags(text):
    text_lower = text.lower()

    countries = [c.name for c in pycountry.countries if c.name not in ["Jersey", "Georgia"]] + ["Taiwan", "Saint Martin", "Iran", "Lao", "Moldova", "Tanzania", "Vatican", "Venezuela", "Korea"]

    foreign_found = set()
    us_found = set()

    # Foreign countries
    for country in countries:
        if country == "Mexico":
            # Match "Mexico" but exclude "New Mexico"
            pattern = r"(?<!new\s)\bmexico\b"
        else:
            pattern = r"\b" + re.escape(country.lower()) + r"\b"

        if re.search(pattern, text_lower):
            if country != "United States":
                foreign_found.add(country)

    # Alternative foreign names
    for country, aliases in ALT_NAMES.items():
        for alias in aliases:
            if re.search(r"\b" + re.escape(alias.lower()) + r"\b", text_lower):
                foreign_found.add(country)

    # US states (full names + abbreviations)
    for state, abbr in US_STATES.items():
        # Default pattern
        pattern = r"\b" + re.escape(state.lower()) + r"\b"
        # Special case: skip "New York" if followed by "Times"
        if state == "New York":
            pattern = r"\bnew york\b(?!\s+times)"

        # Full name match
        if re.search(pattern, text_lower):
            us_found.add(state)

        # Abbreviation match (only parentheses or after comma+space)
        if match_state_abbr(text, state, abbr):
            us_found.add(f"{state} ({abbr})")

    # US regions
    for region in US_REGIONS:
        if re.search(r"\b" + re.escape(region.lower()) + r"\b", text_lower):
            us_found.add(region)

    # US indicators
    for indicator in US_INDICATORS:
        if re.search(r"\b" + re.escape(indicator.lower()) + r"\b", text_lower):
            us_found.add(indicator)

    # Determine flag
    if foreign_found and us_found:
        flag = "BOTH"
    elif foreign_found:
        flag = "FOREIGN_ONLY"
    elif us_found:
        flag = "US_ONLY"
    else:
        flag = "NONE"

    return flag, list(foreign_found), list(us_found)

# --- Apply to DataFrame ---
def flag_country(df):
    flags = df.apply(
        lambda row: find_country_flags(str(row['title']) + " " + str(row['body'])),
        axis=1
    )
    df['country_flag'] = flags.apply(lambda x: x[0])
    df['foreign_countries'] = flags.apply(lambda x: x[1])
    df['us_mentions'] = flags.apply(lambda x: x[2])
    return df
