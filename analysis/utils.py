import matplotlib.pyplot as plt
from collections import Counter
import numpy as np
import pycountry

def compare_histograms(items_list1, items_list2, title, filename, label1='List 1', label2='List 2', scale_counts = True):
    # Count frequencies
    counter1 = Counter(items_list1)
    counter2 = Counter(items_list2)

    # Get all unique labels
    all_labels = sorted(set(counter1.keys()).union(set(counter2.keys())))

    # Total counts for normalization
    total1 = sum(counter1.values())
    total2 = sum(counter2.values())

    if scale_counts:
        # Get frequencies (proportions) for each label (0 if not present)
        freq1 = [counter1.get(label, 0) / total1 for label in all_labels]
        freq2 = [counter2.get(label, 0) / total2 for label in all_labels]
    else:
        # Get frequencies for each label (0 if not present)
        freq1 = [counter1.get(label, 0) for label in all_labels]
        freq2 = [counter2.get(label, 0) for label in all_labels]

    # Set positions for bars
    x = np.arange(len(all_labels))
    width = 0.4  # width of the bars

    # Create the grouped bar chart
    plt.figure(figsize=(24, 8))
    plt.bar(x - width/2, freq1, width, label=label1, color='skyblue')
    plt.bar(x + width/2, freq2, width, label=label2, color='salmon')

    # Formatting
    #plt.xlabel(xlabel, fontsize=18)
    if scale_counts:
        plt.ylabel('Frequency', fontsize=18)
    else:
        plt.ylabel('Count', fontsize=18)
    plt.title(title, fontsize=22)
    plt.xticks(x, all_labels, rotation=45, ha='right', fontsize=18)
    plt.yticks(fontsize=18)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.legend(fontsize=18)
    plt.tight_layout()

    # Save and show
    plt.savefig(filename, dpi=300, facecolor='white', edgecolor='none')
    plt.show()

# Set of U.S. states


# Function to split states and countries
def split_locations(locations):
    us_states = {
        'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado', 'Connecticut',
        'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa',
        'Kansas', 'Kentucky', 'Louisiana', 'Maine', 'Maryland', 'Massachusetts', 'Michigan',
        'Minnesota', 'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada', 'New Hampshire',
        'New Jersey', 'New Mexico', 'New York', 'North Carolina', 'North Dakota', 'Ohio',
        'Oklahoma', 'Oregon', 'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota',
        'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington', 'West Virginia',
        'Wisconsin', 'Wyoming'
    }

    world_countries = [c.name for c in pycountry.countries if c.name not in ["Jersey", "Georgia"]] + ["UK", "Britain", "England", "South Korea", "North Korea", "Iran", "Syria", "Venezuela", "Russia", "Taiwan", "Saint Martin", "Iran", "Lao", "Moldova", "Tanzania", "Vatican", "Venezuela", "Korea"]

    states = []
    countries = []
    other = []

    for loc in locations:
        state_match = next((state for state in us_states if state in loc), None)
        country_match = next((country for country in world_countries if country in loc), None)

        if state_match:
            states.append(state_match)
        elif country_match:
            countries.append(country_match)
        else:
            other.append(loc)

    return states, countries, other


# Flatten and filter location lists
#def flatten_and_filter(locations_column):
 #   return [item for sublist in locations_column for item in sublist if item != "NA"]

from itertools import chain

# Flatten and filter location lists
#def flatten_and_filter(series, exclude="NA"):
#    """Flatten lists in a pandas Series and filter out unwanted values."""
#    return [item for item in chain.from_iterable(series.dropna()) if item != exclude]

def flatten(series):
    """Flatten lists in a pandas Series"""
    return [item for item in chain.from_iterable(series.dropna())]


import re

def extract_region_mentions(text, regions=None):
    """
    Extract mentions of specified U.S. regions from the given text.

    Parameters
    ----------
    text : str
        The input text to search.
    regions : list of str, optional
        A list of region names to search for. If None, defaults to:
        ['Northeast', 'South', 'Midwest', 'Southwest', 'West']

    Returns
    -------
    list of str
        Mentions of regions found in the text, preserving order of appearance.
        Special rule: mentions of 'Mid-Atlantic' are mapped to 'Northeast'.
    """

    mentions = []
    if regions is None:
        regions = ["Northeast", "South", "Midwest", "Southwest", "West"]

        # Special rule: Mid-Atlantic counts as Northeast
        if re.search(r"\bMid-?Atlantic\b", text): # flags=re.IGNORECASE
            mentions.append("Northeast")

    for region in regions:
        pattern = r'\b' + re.escape(region) + r'\b'
        if re.search(pattern, text): # flags=re.IGNORECASE
            mentions.append(region)

    return mentions
