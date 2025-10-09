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

# =================================================================================================================================
# Section Cleaning & Classification Utilities (Guo)
#================================================================================================================================


# ---------- Canonicalization helpers ----------
_NBSP = "\xa0"
_LEAD_QUOTES_RE  = re.compile(r'^[\"\'“”‘’]+')
_TRAIL_PUNCT_RE  = re.compile(r'[,\.;:!\?\"\'“”‘’]+$')
_CANON_REPL = [
    (re.compile(r"\bliesure\b", flags=re.I), "leisure"),
    (re.compile(r"\bweschester\b", flags=re.I), "westchester"),
    (re.compile(r"[_]+$", flags=re.I), ""),         # drop trailing underscores
    (re.compile(r"[–—]", flags=re.I), "-"),         # normalize en/em-dash
    (re.compile(r"\s+/\s+", flags=re.I), "/"),      # normalize spaces around '/'
    (re.compile(r"\s*&\s*", flags=re.I), " & "),    # normalize & spacing
    (re.compile(r"\s+", flags=re.I), " "),          # collapse spaces
]

def _clean_nbsp_and_spaces(text: str) -> str:
    """Replace NBSP with spaces, collapse whitespace, strip ends. Safe for non-str/NaN."""
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return ""
    s = str(text).replace(_NBSP, " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _normalize_token(tok: str) -> str:
    """Strip leading quotes, trailing punctuation, canonical replacements; lowercase (casefold)."""
    s = str(tok)
    s = _LEAD_QUOTES_RE.sub("", s)
    s = _TRAIL_PUNCT_RE.sub("", s).strip()
    for patt, repl in _CANON_REPL:
        s = patt.sub(repl, s)
    return s.casefold()

# ---------- single-value cleaner ----------
def clean_section(section: str) -> str | None:
    """
    Clean a single section string (format-level cleaning only).
    Returns None if empty after cleaning.
    """
    s = _clean_nbsp_and_spaces(section)
    if not s:
        return None
    s = _normalize_token(s)
    return s if s else None

# ---------- Tokenization & noise filtering ----------
NOISE_RE = re.compile(
    r"(?i)^(?:"
    r"column\s*\d+|"                          # column 0/1/2...
    r"pg$|"                                   # bare 'pg'
    r"pg\.?\s*(?:[A-Z]?-?[0-9]+[A-Z]*|web)|"  # pg. 1a / pg. a-1 / pg. 3 / pg. web
    r"page\s+\d+|"                            # page 1
    r"section(?:\s+[A-Z0-9]+)?|"              # section / section A / section 1
    r"asection|"                              # asection
    r"front[_ ]page|web|"                     # front_page / front page / web
    r"submitted content|cover story|specialsections|fence post|"  # packaging
    r"timeout|time\s*out!?|go!|"              # time out!, go!
    r"part\s+\d+"                             # part 1/2...
    r")$"
)

def _split_tokens(section_text: str) -> list[str]:
    """Split by ';', trim, drop empties (string in → list out)."""
    s = _clean_nbsp_and_spaces(section_text)
    if not s:
        return []
    tokens = [t.strip() for t in s.split(";")]
    return [t for t in tokens if t]

def _filter_and_normalize(tokens: list[str]) -> list[str]:
    """Remove layout/packaging noise with NOISE_RE; normalize each token."""
    out: list[str] = []
    for t in tokens:
        t = re.sub(r"_+$", "", t)
        t = re.sub(r"\s+", " ", t).strip()
        t = _TRAIL_PUNCT_RE.sub("", t).strip()
        if not t or NOISE_RE.match(t):
            continue
        k = _normalize_token(t)
        if k:
            out.append(k)
    return out

# ---------- Categories & mappings (desk-first, then keyword) ----------
CATEGORIES = [
    "World/International",
    "US/National",
    "Metro/Local",
    "Business/Finance",
    "Sports",
    "Arts/Culture",
    "Style/Life/Fashion",
    "Opinion/Editorial/Letters",
    "books/podcast",
    "Science/Health/Tech",
]

DESK_MAP = {
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
    "leisure/weekend desk": "Arts/Culture",
    "weekend desk": "Arts/Culture",
    "movies, performing arts/weekend desk": "Arts/Culture",
    "dining, dining out/cultural desk": "Arts/Culture",

    # Style / Life / Fashion
    "style desk": "Style/Life/Fashion",
    "real estate desk": "Style/Life/Fashion",
    "travel desk": "Style/Life/Fashion",
    "dining in, dining out/style desk": "Style/Life/Fashion",
    "dining in, dining out / style desk": "Style/Life/Fashion",
    "house & home/style desk": "Style/Life/Fashion",
    "living desk": "Style/Life/Fashion",
    "home desk": "Style/Life/Fashion",
    "society desk": "Style/Life/Fashion",
    "magazine desk": "Style/Life/Fashion",

    # Opinion / Editorial / Letters
    "editorial desk": "Opinion/Editorial/Letters",
    "sunday review desk": "Opinion/Editorial/Letters",
    "week in review desk": "Opinion/Editorial/Letters",

    # books / podcast
    "book review desk": "books/podcast",

    # Science / Tech / Health
    "science desk": "Science/Health/Tech",
}

KEYWORD_MAP = {
    # US / National
    "us": "US/National",
    "national": "US/National",
    "politics": "US/National",
    "the upshot": "US/National",
    "upshot": "US/National",
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
    "classified": "Business/Finance",
    "classifieds": "Business/Finance",
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

    # Arts / Culture
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

    # LifeStyle
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
    "then & now": "LifeStyle",
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
    "realestate": "LifeStyle",
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

    # books / podcast
    "books": "books/podcast",
    "transcript": "books/podcast",
    "podcast": "books/podcast",
    "podcasts": "books/podcast",

    # Science / Tech / Health
    "well": "Science/Health/Tech",
    "technology": "Science/Health/Tech",
    "health, science, medicine & technology": "Science/Health/Tech",
    "science, medicine, technology": "Science/Health/Tech",
    "ohiotech": "Science/Health/Tech",
    "health": "Science/Health/Tech",
}

# ======================
# Classifier: Desk-first, then Keyword , else None
# ======================
def classify_section(section_text: str) -> str | None:
    if pd.isna(section_text) or not str(section_text).strip():
        return None

    tokens = [t.strip() for t in str(section_text).split(";") if t.strip()]
    if not tokens:
        return None

    desk_hits, kw_hits = set(), set()

    for t in tokens:
        # filter layout/packaging noise
        if NOISE_RE.match(t.strip()):
            continue
        k = normalize_token(t)
        if not k:
            continue
        if k in DESK_MAP:
            desk_hits.add(DESK_MAP[k])
        if k in KEYWORD_MAP:
            kw_hits.add(KEYWORD_MAP[k])

    # Desk-first
    if len(desk_hits) == 1:
        return next(iter(desk_hits))
    if len(desk_hits) > 1:
        return None   # conflicting desks → abstain

    # Keyword fallback (books/podcast priority)
    if len(kw_hits) >= 1:
        if "books/podcast" in kw_hits:
            return "books/podcast"
        return next(iter(kw_hits)) if len(kw_hits) == 1 else None

    return None

# ---------- DataFrame entry point ----------
def add_section_category(
    df: pd.DataFrame,
    source_col: str = "section",
    dest_col: str = "category",
    cleaned_col: str | None = None
) -> pd.DataFrame:
    """
    Add a category column to df using classify_section.
    - If cleaned_col exists, use it; else use source_col.
    Returns a new DataFrame; original is not modified.
    """
    d = df.copy()
    input_col = cleaned_col if (cleaned_col and cleaned_col in d.columns) else source_col
    d[dest_col] = d[input_col].apply(classify_section)
    return d

__all__ = ["clean_section", "classify_section", "add_section_category"]
