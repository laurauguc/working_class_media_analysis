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

# old version
# --- Function to check countries/flags in text ---
def find_country_flags_old(text):
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



# version 2:
import re
import json
import pycountry
from pathlib import Path

def find_country_flags(text):
    text_lower = text.lower()

    # === Country list (filtered and supplemented) ===
    countries = [c.name for c in pycountry.countries if c.name not in ["Jersey", "Georgia"]] + [
        "Taiwan", "Saint Martin", "Iran", "Lao", "Moldova", "Tanzania", "Vatican",
        "Venezuela", "Korea"
    ]

    # === Load world capitals from a static JSON file ===
    # Download: https://github.com/samayo/country-json/blob/master/src/country-by-capital-city.json
    capitals_path = Path("country-by-capital-city.json")
    WORLD_CAPITALS = []

    if capitals_path.exists():
        with open(capitals_path, encoding="utf-8") as f:
            data = json.load(f)
            WORLD_CAPITALS = [entry["city"] for entry in data if entry.get("city")]
    else:
        print("⚠️ Warning: country-by-capital-city.json not found. Capitals will be skipped.")

    # === Geopolitical / regional groupings ===
    REGIONS = [
        "European Union", "EU", "Asia", "Middle East",
        "Latin America", "Central America", "North Africa", "Southern Africa",
        "Western Europe", "Eastern Europe", "Central Europe", "Scandinavia",
        "Nordic countries", "Caribbean", "Pacific Islands", "South America",
        "Africa", "Asia", "Europe", "Oceania", "Antarctica"
    ]

    foreign_found = set()
    us_found = set()

    # === Foreign countries ===
    for country in countries:
        if country == "Mexico":
            pattern = r"(?<!new\s)\bmexico\b"
        else:
            pattern = r"\b" + re.escape(country.lower()) + r"\b"
        if re.search(pattern, text_lower):
            if country != "United States":
                foreign_found.add(country)

    # === Alternative names (if provided globally) ===
    if 'ALT_NAMES' in globals():
        for country, aliases in ALT_NAMES.items():
            for alias in aliases:
                if re.search(r"\b" + re.escape(alias.lower()) + r"\b", text_lower):
                    foreign_found.add(country)

    # === World capitals ===
    for cap in WORLD_CAPITALS:
        if re.search(r"\b" + re.escape(cap.lower()) + r"\b", text_lower):
            foreign_found.add(cap + " (Capital)")

    # === Regions ===
    for region in REGIONS:
        if re.search(r"\b" + re.escape(region.lower()) + r"\b", text_lower):
            foreign_found.add(region)

    # === US states (if available) ===
    if 'US_STATES' in globals():
        for state, abbr in US_STATES.items():
            pattern = r"\b" + re.escape(state.lower()) + r"\b"
            if state == "New York":
                pattern = r"\bnew york\b(?!\s+times)"
            if re.search(pattern, text_lower):
                us_found.add(state)
            if 'match_state_abbr' in globals() and callable(match_state_abbr):
                if match_state_abbr(text, state, abbr):
                    us_found.add(f"{state} ({abbr})")

    # === US regions / indicators (if available) ===
    if 'US_REGIONS' in globals():
        for region in US_REGIONS:
            if re.search(r"\b" + re.escape(region.lower()) + r"\b", text_lower):
                us_found.add(region)

    if 'US_INDICATORS' in globals():
        for indicator in US_INDICATORS:
            if re.search(r"\b" + re.escape(indicator.lower()) + r"\b", text_lower):
                us_found.add(indicator)

    # === Determine flag ===
    if foreign_found and us_found:
        flag = "BOTH"
    elif foreign_found:
        flag = "FOREIGN_ONLY"
    elif us_found:
        flag = "US_ONLY"
    else:
        flag = "NONE"

    return flag, sorted(foreign_found), sorted(us_found)



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


#### Near duplicates


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

def find_near_duplicates_same_publisher(df_articles, threshold):
    df_articles = df_articles.copy()
    df_articles.loc[:, "publisher_clean"] = df_articles["publisher"].apply(clean_publisher)
    #df_articles["publisher_clean"] = df_articles["publisher"].apply(clean_publisher)
    # Duplicate Detection
    df_out = (
        df_articles.groupby("publisher_clean", sort=False, group_keys=False)
        .apply(lambda g: mark_duplicates(g, threshold))
    )

    near_dup_mask = df_out["near_duplicate"]
    return near_dup_mask


# =================================================================================================================================
# Section Cleaning & Classification （Guo）
#================================================================================================================================

import re
import pandas as pd

# ---------- Prep Tool ----------
_NBSP = "\xa0" #non-breaking space
_LEAD_QUOTES_RE = re.compile(r'^[\"\'“”‘’]+') #deal with different style of quotes 
_TRAIL_PUNCT_RE = re.compile(r'[,\.;:!\?\"\'“”‘’]+$') #deal with other marks


# ---------- Step A: Normalize ----------
_CANON_REPL = [
    (re.compile(r"\bliesure\b", re.I), "leisure"),
    (re.compile(r"\bweschester\b", re.I), "westchester"),
    (re.compile(r"[_]+$", re.I), ""),           # drop trailing underscores
    (re.compile(r"[–—]", re.I), "-"),           # normalize en/em-dash to "-"
    (re.compile(r"\s*-\s*", re.I), "-"),        # unify spaces around '-'
    (re.compile(r"\s*/\s*", re.I), "/"),        # unify spaces around '/'
    (re.compile(r"\s*&\s*", re.I), " & "),      # unify spaces around '&'
    (re.compile(r"\s+", re.I), " "),            # collapse spaces
]

def _clean_nbsp_and_spaces(text) -> str:
    """NORM · NA-safe → NBSP replace → whitespace collapse."""
    try:
        if pd.isna(text):
            return ""
    except TypeError:
        pass
    if text is None:
        return ""
    s = str(text).replace(_NBSP, " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _normalize_token(tok: str) -> str:
    """NORM · per-token clean → trim quotes/punct → canonicalize → casefold."""
    s = _clean_nbsp_and_spaces(tok)
    if not s:
        return ""
    s = _LEAD_QUOTES_RE.sub("", s)
    s = _TRAIL_PUNCT_RE.sub("", s).strip()
    for patt, repl in _CANON_REPL:
        s = patt.sub(repl, s)
    return s.casefold()

# ---------- Step B: FILTERING ----------
NOISE_RE = re.compile(
    r"(?i)^(?:"
    r"column\s*\d+|"
    r"pg$|"
    r"pg\.?\s*(?:[A-Z]?-?[0-9]+[A-Z]*|web)|"
    r"page\s+\d+|"
    r"section(?:\s+[A-Z0-9]+)?|"
    r"asection|"
    r"front[_ ]page|web|"
    r"submitted content|cover story|specialsections|fence post|"
    r"timeout|time\s*out!?|go!|"
    r"part\s+\d+"
    r")$"
)


# ---------- Step C: Categories & mappings dictionary (desk-first, then keyword) ----------
CATEGORIES = [
    "World/International",
    "US/National",
    "Metro/Local",
    "Business/Finance",
    "Sports",
    "Arts/Culture",
    "LifeStyle", 
    "Opinion/Editorial/Letters",
    "Science/Health/Tech", #number really small, might remove and try to reduce more
]

# DESK map (books → Arts/Culture; no 'podcast' category)
_DESK_MAP_RAW = {
    # Metro / Local
    "metropolitan desk": "Metro/Local",
    "nyregion": "Metro/Local",
    "new jersey weekly desk": "Metro/Local",
    "long island weekly desk": "Metro/Local",
    "connecticut weekly desk": "Metro/Local",
    "westchester weekly desk": "Metro/Local",
    "the city weekly desk": "Metro/Local",
    "pennsylvania voters guide": "Metro/Local",

    # World / International
    "foreign desk": "World/International",

    # US / National
    "national desk": "US/National",

    # Business / Finance
    "business/financial desk": "Business/Finance",
    "financial desk": "Business/Finance",
    "money and business/financial desk": "Business/Finance",
    "personal investing supplement desk": "Business/Finance",

    # Sports
    "sports desk": "Sports",

    # Arts / Culture
    "the arts/cultural desk": "Arts/Culture",
    "arts and leisure desk": "Arts/Culture",
    "arts & leisure desk": "Arts/Culture",
    "arts & ideas/cultural desk": "Arts/Culture",
    "cultural desk": "Arts/Culture",
    "cultural desk - summertimes supplement": "Arts/Culture",
    "movies, performing arts/weekend desk": "Arts/Culture",
    "dining, dining out/cultural desk": "Arts/Culture",
    "book review desk": "Arts/Culture",  # changed from books/podcast

    # LifeStyle
    "style desk": "LifeStyle",
    "real estate desk": "LifeStyle",
    "leisure/weekend desk": "LifeStyle",
    "weekend desk": "LifeStyle",
    "travel desk": "LifeStyle",
    "dining in, dining out/style desk": "LifeStyle",
    "dining in, dining out / style desk": "LifeStyle",
    "house & home/style desk": "LifeStyle",
    "living desk": "LifeStyle",
    "home desk": "LifeStyle",
    "society desk": "LifeStyle",
    "magazine desk": "LifeStyle",

    # Opinion / Editorial / Letters
    "editorial desk": "Opinion/Editorial/Letters",
    "sunday review desk": "Opinion/Editorial/Letters",
    "week in review desk": "Opinion/Editorial/Letters",

    # Science / Tech / Health
    "science desk": "Science/Health/Tech",
}

# KEYWORD map (no 'podcast'/'podcasts'/'transcript'; 'books' → Arts/Culture)
_KEYWORD_MAP_RAW = {
    # US / National
    "us": "US/National",
    "national": "US/National",
    "politics": "US/National",
    "the upshot": "US/National",
    "upshot": "US/National", #https://www.nytimes.com/section/upshot
    "nytnow": "US/National",
    "minnesota poll": "US/National",
    "state": "US/National",
    "nation": "US/National",
    "national weekly": "US/National",

    # World / International
    "world": "World/International",
    "europe": "World/International",
    "china": "World/International",
    "nation & world extra": "World/International",
    "infoplus: world up close": "World/International",
    "nation world": "World/International",
    "nation & world": "World/International",

    # Metro / Local
    "local": "Metro/Local",
    "neighbor": "Metro/Local",
    "neighbors": "Metro/Local",
    "philadelphia": "Metro/Local",
    "south jersey": "Metro/Local",
    "new jersey": "Metro/Local",
    "connecticut": "Metro/Local",
    "region": "Metro/Local",
    "the region": "Metro/Local",
    "philly & region": "Metro/Local",
    "dayton": "Metro/Local",
    "beavercreek fairborn and xenia": "Metro/Local",
    "huber heights riverside dayton and vandalia": "Metro/Local",
    "west montgomery county": "Metro/Local",
    "manayunk": "Metro/Local",
    "southwest": "Metro/Local",
    "the gazette": "Metro/Local",
    "city & region": "Metro/Local",
    "metro": "Metro/Local",
    "local news philadelphia & its suburbs": "Metro/Local",
    "neighbors montgomery": "Metro/Local",
    "metro today": "Metro/Local",

    # Business / Finance
    "business": "Business/Finance",
    "business wire": "Business/Finance",
    "marketplace": "Business/Finance",
    "money": "Business/Finance",
    "biz ledger": "Business/Finance",
    "classified": "Business/Finance", #ads
    "classifieds": "Business/Finance", #ads
    "job market": "Business/Finance",
    "your-money": "Business/Finance",
    "retirement": "Business/Finance",
    "budgets": "Business/Finance",
    "philadelphia business": "Business/Finance",

    # Sports
    "sports": "Sports",
    "sports-high schools": "Sports",
    "sportsweekend": "Sports",
    "sportsxtra": "Sports",

    # Arts / Culture (all movies/books go here
    "arts & entertainment": "Arts/Culture",
    "arts and entertainment": "Arts/Culture",
    "arts": "Arts/Culture",
    "p-com ent. entertainment": "Arts/Culture",
    "movies": "Arts/Culture",
    "movie review": "Arts/Culture",
    "television": "Arts/Culture",
    "variety": "Arts/Culture",
    "entertainment": "Arts/Culture",
    "theater": "Arts/Culture",
    "features magazine: entertainment": "Arts/Culture",
    "features magazine / entertainment": "Arts/Culture",
    "features entertainment": "Arts/Culture",
    "features arts & entertainment": "Arts/Culture",
    "inq arts & entertainment": "Arts/Culture",
    "museums": "Arts/Culture",
    "screening room": "Arts/Culture",
    "history extra": "Arts/Culture",
    "play": "Arts/Culture",
    "watching": "Arts/Culture",
    "life & arts": "Arts/Culture",
    "books": "Arts/Culture",  

    # LifeStyle : travel & home decor & cars & fashion & food
    "life": "LifeStyle",
    "lifestyles": "LifeStyle",
    "lifestyle": "LifeStyle",
    "travel": "LifeStyle",
    "magazine": "LifeStyle",
    "style": "LifeStyle",
    "dining": "LifeStyle",
    "features weekend": "LifeStyle",
    "weekender": "LifeStyle",
    "escapes": "LifeStyle",
    "food": "LifeStyle",
    "suburban living": "LifeStyle",
    "real estate": "LifeStyle",
    "t magazine": "LifeStyle",
    "t: women's fashion magazine": "LifeStyle",
    "t: men's fashion magazine": "LifeStyle",
    "t: travel magazine": "LifeStyle",
    "features magazine": "LifeStyle",
    "features": "LifeStyle",
    "features lifestyle": "LifeStyle",
    "features image": "LifeStyle",
    "features magazine: lifestyle": "LifeStyle",
    "features magazine: home & design": "LifeStyle",
    "features home & design": "LifeStyle",
    "features travel": "LifeStyle",
    "thursday styles": "LifeStyle",
    "tstyle": "LifeStyle",
    "styles of the times": "LifeStyle",
    "parenting": "LifeStyle",
    "going places": "LifeStyle",
    "what to do": "LifeStyle",
    "leisure": "LifeStyle",
    "summer times supplement": "LifeStyle",
    "spring times supplement": "LifeStyle",
    "live life love": "LifeStyle",
    "key magazine": "LifeStyle",
    "craig laban s ultimate dining": "LifeStyle",
    "road less traveled": "LifeStyle",
    "automobiles": "LifeStyle",
    "motoring": "LifeStyle",
    "cars": "LifeStyle",
    "auto showcase": "LifeStyle",
    "auto": "LifeStyle",
    "realestate": "LifeStyle", # could go to business?
    "t-magazine": "LifeStyle",
    "fashion": "LifeStyle",
    "sophisticated traveler magazine": "LifeStyle",
    "variety / freetime": "LifeStyle",
    "freetime": "LifeStyle",

    # Opinion / Editorial / Letters
    "opinion": "Opinion/Editorial/Letters",
    "opinions": "Opinion/Editorial/Letters",
    "editorial": "Opinion/Editorial/Letters",
    "op-ed": "Opinion/Editorial/Letters",
    "oped": "Opinion/Editorial/Letters",
    "op-ed columnist": "Opinion/Editorial/Letters",
    "op-ed contributor": "Opinion/Editorial/Letters",
    "letters": "Opinion/Editorial/Letters",
    "letter": "Opinion/Editorial/Letters",
    "letters to the editor": "Opinion/Editorial/Letters",
    "currents-editorial": "Opinion/Editorial/Letters",
    "community voices": "Opinion/Editorial/Letters",
    "sunday review": "Opinion/Editorial/Letters",
    "ideas & voices": "Opinion/Editorial/Letters",
    "ideas voices": "Opinion/Editorial/Letters",
    "p-com opinion": "Opinion/Editorial/Letters",

    # Science / Tech / Health
    "well": "Science/Health/Tech",
    "technology": "Science/Health/Tech",
    "health, science, medicine & technology": "Science/Health/Tech",
    "science, medicine, technology": "Science/Health/Tech",
    "ohiotech": "Science/Health/Tech",
    "health": "Science/Health/Tech",
}

def _normalize_map_keys(raw: dict) -> dict:
    """NORM · apply the same normalization to mapping keys (built once at import)."""
    out: dict[str, str] = {}
    for k, v in raw.items():
        nk = _normalize_token(k)
        if nk:
            out[nk] = v
    return out

# Build normalized maps ONCE to align key-space with token normalization
DESK_MAP = _normalize_map_keys(_DESK_MAP_RAW)
KEYWORD_MAP = _normalize_map_keys(_KEYWORD_MAP_RAW)

# ---------- Step D: add category column to dataset ----------
def add_section_category(
    df: pd.DataFrame,
    source_col: str = "section",
    dest_col: str = "category",
    return_cleaned: bool = False,
    cleaned_col: str = "section_cleaned"
) -> pd.DataFrame:
    """
    Apply desk-first-then-keyword classification to a DataFrame column.

    Logic:
      - Normalize the cell text (NA-safe, NBSP, trim, canonicalize, casefold)
      - Split on ';' to candidate tokens
      - Normalize each token, then drop layout/packaging noise (NOISE_RE)
      - Desk-first decision; if none, keyword fallback with deterministic order
      - Return None if ambiguous or no signal
      - Optionally emit a normalized column for QA (return_cleaned=True)
    """
    if source_col not in df.columns:
        raise KeyError(f"Column '{source_col}' not in DataFrame")

    def _classify_cell(text) -> str | None:
        # Normalize the raw cell (coarse level)
        s = _clean_nbsp_and_spaces(text)
        if not s:
            return None

        # Split into tokens
        raw_tokens = [t for t in (tok.strip() for tok in s.split(";")) if t]
        if not raw_tokens:
            return None

        # Normalize tokens and filter layout noise
        norm_tokens: list[str] = []
        for t in raw_tokens:
            k = _normalize_token(t)
            if not k or NOISE_RE.match(k):
                continue
            norm_tokens.append(k)
        if not norm_tokens:
            return None

        # Mapping & resolution
        desk_hits: set[str] = set()
        kw_hits: set[str] = set()
        for k in norm_tokens:
            if k in DESK_MAP:
                desk_hits.add(DESK_MAP[k])
            if k in KEYWORD_MAP:
                kw_hits.add(KEYWORD_MAP[k])

        # Desk-first
        if len(desk_hits) == 1:
            return next(iter(desk_hits))
        if len(desk_hits) > 1:
            return None  # conflicting desks → abstain

        # If no desk match, then move to Keyword match
        if kw_hits:
            for cat in CATEGORIES:
                if cat in kw_hits:
                    return cat
            return sorted(kw_hits)[0]

        return None

    d = df.copy()

    # Optional audit column with normalized text
    if return_cleaned:
        d[cleaned_col] = d[source_col].apply(_normalize_token)
        input_col = cleaned_col
    else:
        input_col = source_col

    d[dest_col] = d[input_col].apply(_classify_cell)
    return d

__all__ = ["add_section_category"]