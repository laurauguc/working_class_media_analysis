import matplotlib.pyplot as plt
from collections import Counter
import numpy as np
import pycountry
import os
from docx import Document
import re
import seaborn as sns
from itertools import chain
import json
import time
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def compare_histograms(items_list1, items_list2, title, filename,
                       label1='List 1', label2='List 2',
                       scale_counts=True, order_by_count=False, ylabel = None):
    # Count frequencies
    counter1 = Counter(items_list1)
    counter2 = Counter(items_list2)

    # Get all unique labels
    all_labels = list(set(counter1.keys()).union(set(counter2.keys())))

    # Total counts for normalization
    total1 = sum(counter1.values())
    total2 = sum(counter2.values())

    if scale_counts:
        # Frequencies as percentages
        freq1_dict = {label: (counter1.get(label, 0) / total1) * 100 for label in all_labels}
        freq2_dict = {label: (counter2.get(label, 0) / total2) * 100 for label in all_labels}
    else:
        # Raw counts
        freq1_dict = {label: counter1.get(label, 0) for label in all_labels}
        freq2_dict = {label: counter2.get(label, 0) for label in all_labels}

    # Optionally reorder labels by highest total frequency or count
    if order_by_count:
        all_labels = sorted(
            all_labels,
            key=lambda lbl: freq1_dict[lbl] + freq2_dict[lbl],
            reverse=True
        )
    else:
        all_labels = sorted(all_labels)

    # Get ordered frequencies
    freq1 = [freq1_dict[label] for label in all_labels]
    freq2 = [freq2_dict[label] for label in all_labels]

    # Set positions for bars
    x = np.arange(len(all_labels))
    width = 0.4  # width of the bars

    # Create the grouped bar chart
    plt.figure(figsize=(24, 8))
    plt.bar(x - width/2, freq1, width, label=label1, color='skyblue')
    plt.bar(x + width/2, freq2, width, label=label2, color='salmon')

    # Formatting
    if ylabel is None:
        ylabel = 'Percentage of Articles (%)' if scale_counts else 'Count'
    plt.ylabel(ylabel, fontsize=18)
    plt.title(title, fontsize=22)
    plt.xticks(x, all_labels, rotation=45, ha='right', fontsize=18)
    plt.yticks(fontsize=18)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.legend(fontsize=18)
    plt.tight_layout()

    # Save and show
    plt.savefig(filename, dpi=300, facecolor='white', edgecolor='none')
    plt.show()

def line_time_plot(
    df_articles_with_results,
    nyt_mask,
    variable,
    title,
    filename,
    variable_label=None,
    smooth_window=3  # rolling average window; set to None to disable
):
    """
    Plot two line charts showing the percentage of articles per year, grouped by a categorical variable:
    one for NYT and one for other publishers, with consistent colors. Optionally smooth lines.

    Parameters
    ----------
    df_articles_with_results : pandas.DataFrame
        DataFrame containing a 'year' column and the specified categorical variable.
    nyt_mask : pandas.Series[bool]
        Boolean mask selecting NYT articles.
    variable : str
        Column name of the categorical variable.
    title : str
        Base title for the plots.
    variable_label : str, optional
        Label to use for the variable in the legend. Defaults to `variable` if None.
    smooth_window : int or None, optional
        Rolling window size for smoothing lines. If None, no smoothing is applied.
    """
    if variable_label is None:
        variable_label = variable

    # Determine all categories
    all_categories = df_articles_with_results[variable].dropna().unique()

    # Use a clean, pretty color palette
    palette = sns.color_palette("tab10", n_colors=len(all_categories))
    colors = {cat: palette[i] for i, cat in enumerate(all_categories)}

    fig, axes = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

    for ax, mask, subtitle in zip(
        axes,
        [nyt_mask, ~nyt_mask],
        [f"NYT: {title}", f"Other Publishers: {title}"]
    ):
        # Count articles per (year, variable)
        grouped = (
            df_articles_with_results[mask]
            .groupby(["year", variable])
            .size()
            .unstack(fill_value=0)
        )

        # Reindex columns to ensure consistent category order
        grouped = grouped.reindex(columns=all_categories, fill_value=0)

        # Convert to yearly percentages
        grouped = grouped.div(grouped.sum(axis=1), axis=0) * 100

        # Optionally smooth with rolling average
        if smooth_window is not None and smooth_window > 1:
            grouped = grouped.rolling(window=smooth_window, min_periods=1).mean()

        # Plot each category as a line
        for cat in grouped.columns:
            ax.plot(
                grouped.index,
                grouped[cat],
                label=cat,
                color=colors[cat],
                linewidth=2,
                alpha=0.9
            )

        ax.set_ylabel("Percentage of Articles (%)")
        ax.set_title(subtitle)
        ax.grid(True, linestyle="--", alpha=0.7)
        ax.legend(title=variable_label, bbox_to_anchor=(1.05, 1), loc="upper left", ncol=2)

    axes[-1].set_xlabel("Year")
    plt.tight_layout()

    # Save and show
    plt.savefig(filename, dpi=300, facecolor='white', edgecolor='none')
    plt.show()

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

    world_countries = [c.name for c in pycountry.countries if c.name not in ["Jersey", "Georgia"]] + ["UK", "Britain", "England", "South Korea", "North Korea", "Iran", "Syria", "Venezuela", "Russia", "Taiwan", "Saint Martin", "Iran", "Lao", "Moldova", "Tanzania", "Vatican", "Venezuela", "Korea", "Turkey", "Czechoslovakia", "Congo"]

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

import matplotlib.pyplot as plt

def stacked_time_plot(df_articles_with_results, nyt_mask, variable, title):
    """
    Plot two stacked bar charts of article counts per year, grouped by a categorical variable:
    one for NYT and one for other publishers, with consistent color coding.
    """
    # Ensure consistent categories and color mapping
    all_categories = (
        df_articles_with_results[variable]
        .value_counts()
        .index
    )

    color_map = plt.colormaps.get_cmap("Set2").resampled(len(all_categories))
    colors = {cat: color_map(i) for i, cat in enumerate(all_categories)}

    fig, axes = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

    for ax, mask, subtitle in zip(
        axes,
        [nyt_mask, ~nyt_mask],
        [f"NYT: {title}", f"Other Publishers: {title}"],
    ):
        grouped = (
            df_articles_with_results[mask]
            .groupby(["year", variable])
            .size()
            .unstack(fill_value=0)
        )

        # Reorder columns to match global order
        grouped = grouped.reindex(columns=all_categories, fill_value=0)

        grouped.plot(
            kind="bar",
            stacked=True,
            ax=ax,
            color=[colors[cat] for cat in grouped.columns],
        )

        ax.set_ylabel("Frequency")
        ax.set_title(subtitle)
        ax.tick_params(axis="x", rotation=45)
        ax.grid(axis="y", linestyle="--", alpha=0.7)
        ax.legend(title=variable, bbox_to_anchor=(1.05, 1), loc="upper left")

    axes[-1].set_xlabel("Year")
    plt.tight_layout()
    plt.show()

# ============================================================================
# TIME ANALYSIS FUNCTIONS
# ============================================================================

def plot_overall_time_distribution(df, save_static=True, save_interactive=True, 
                                   filename_static='time_distribution_static.png',
                                   filename_interactive='time_distribution_interactive.html'):
    """
    Create comprehensive visualizations of article distribution over time.
    
    Generates both static (matplotlib) and interactive (plotly) visualizations showing:
    - Yearly article counts as bar chart
    - Monthly article trends as line/area chart
    - Interactive time series with range selector
    
    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame containing 'year' and 'year_month' columns
    save_static : bool, optional
        Whether to save static matplotlib figure (default: True)
    save_interactive : bool, optional
        Whether to display interactive plotly figure (default: True)
    filename_static : str, optional
        Filename for static plot (default: 'time_distribution_static.png')
    filename_interactive : str, optional
        Filename for interactive plot (default: 'time_distribution_interactive.html')
        
    Returns
    -------
    None
        Displays and optionally saves visualizations
    """
    # Static visualization with matplotlib
    if save_static:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        
        # Yearly distribution
        yearly_counts = df['year'].value_counts().sort_index()
        ax1.bar(yearly_counts.index, yearly_counts.values, color='skyblue', alpha=0.7)
        ax1.set_title('Article Distribution by Year', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Year')
        ax1.set_ylabel('Number of Articles')
        ax1.grid(axis='y', alpha=0.3)
        
        # Monthly distribution
        monthly_counts = df.groupby('year_month').size()
        ax2.plot(monthly_counts.index.to_timestamp(), monthly_counts.values, 
                color='darkblue', linewidth=1.5)
        ax2.set_title('Article Distribution by Month Over Time', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Date')
        ax2.set_ylabel('Number of Articles')
        ax2.grid(alpha=0.3)
        ax2.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig(filename_static, dpi=300, bbox_inches='tight')
        plt.show()
    
    # Interactive visualization with plotly
    if save_interactive:
        monthly_counts = df.groupby('year_month').size()
        monthly_df = pd.DataFrame({
            'Date': monthly_counts.index.to_timestamp(),
            'Article_Count': monthly_counts.values
        })
        
        fig_interactive = go.Figure()
        
        fig_interactive.add_trace(go.Scatter(
            x=monthly_df['Date'],
            y=monthly_df['Article_Count'],
            mode='lines+markers',
            name='Articles per Month',
            line=dict(color='darkblue', width=2),
            marker=dict(size=4),
            hovertemplate='<b>Date:</b> %{x|%Y-%m}<br>' +
                          '<b>Articles:</b> %{y}<br>' +
                          '<extra></extra>'
        ))
        
        fig_interactive.update_layout(
            title='Interactive Article Distribution by Month Over Time',
            xaxis_title='Date',
            yaxis_title='Number of Articles',
            hovermode='x unified',
            showlegend=False,
            width=900,
            height=500,
            template='plotly_white',
            xaxis=dict(
                rangeselector=dict(
                    buttons=list([
                        dict(count=1, label="1Y", step="year", stepmode="backward"),
                        dict(count=5, label="5Y", step="year", stepmode="backward"),
                        dict(count=10, label="10Y", step="year", stepmode="backward"),
                        dict(step="all")
                    ])
                ),
                rangeslider=dict(visible=True),
                type="date"
            )
        )
        
        fig_interactive.show()


def plot_publisher_time_distribution(df, publisher_counts):
    """
    Create multiple visualizations comparing article distribution across publishers over time.
    
    Generates four different views:
    1. Side-by-side bar charts for each publisher
    2. Stacked bar chart showing combined distribution
    3. Line plot comparing trends
    4. Stacked area chart for monthly distribution
    
    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame with 'publisher', 'year', and 'year_month' columns
    publisher_counts : pandas.Series
        Series containing article counts per publisher
        
    Returns
    -------
    None
        Displays visualizations
    """
    print(f"\n{'-'*60}")
    print("ARTICLE DISTRIBUTION BY PUBLISHER OVER TIME")
    print(f"{'-'*60}")
    
    # 1. Individual publisher bar charts
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    colors = ['steelblue', 'darkred']
    publishers = publisher_counts.index.tolist()
    
    for i, publisher in enumerate(publishers):
        publisher_data = df[df['publisher'] == publisher]
        yearly_pub_counts = publisher_data['year'].value_counts().sort_index()
        
        axes[i].bar(yearly_pub_counts.index, yearly_pub_counts.values, 
                   color=colors[i], alpha=0.7)
        axes[i].set_title(f'{publisher}\n({publisher_counts[publisher]:,} articles)', 
                         fontsize=12, fontweight='bold')
        axes[i].set_xlabel('Year')
        axes[i].set_ylabel('Articles')
        axes[i].grid(axis='y', alpha=0.3)
        axes[i].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.show()
    
    # 2. Stacked bar chart
    fig, ax = plt.subplots(figsize=(15, 8))
    
    nyt_data = df[df['publisher'] == 'New York Times']
    other_data = df[df['publisher'] == 'Other publisher']
    
    nyt_yearly = nyt_data['year'].value_counts().sort_index()
    other_yearly = other_data['year'].value_counts().sort_index()
    
    all_years = sorted(set(nyt_yearly.index) | set(other_yearly.index))
    nyt_counts = [nyt_yearly.get(year, 0) for year in all_years]
    other_counts = [other_yearly.get(year, 0) for year in all_years]
    
    width = 0.8
    ax.bar(all_years, other_counts, width, label='Other Publishers', 
           color='#FF6B6B', alpha=0.8)
    ax.bar(all_years, nyt_counts, width, bottom=other_counts, 
           label='New York Times', color='#4ECDC4', alpha=0.8)
    
    ax.set_xlabel('Year', fontsize=12)
    ax.set_ylabel('Number of Articles', fontsize=12)
    ax.set_title('Article Distribution: Stacked View of Publishers Over Time', 
                 fontsize=14, fontweight='bold')
    ax.legend(loc='upper right')
    ax.grid(axis='y', alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
    
    # 3. Line plot comparison
    plt.figure(figsize=(15, 8))
    for i, publisher in enumerate(publishers):
        publisher_data = df[df['publisher'] == publisher]
        yearly_pub_counts = publisher_data['year'].value_counts().sort_index()
        
        plt.plot(yearly_pub_counts.index, yearly_pub_counts.values, 
                 marker='o', linewidth=3, label=f'{publisher} ({publisher_counts[publisher]:,})', 
                 color=colors[i])
    
    plt.title('Article Trends: New York Times vs Other Publishers', fontsize=14, fontweight='bold')
    plt.xlabel('Year')
    plt.ylabel('Number of Articles')
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()
    
    # 4. Monthly stacked area chart
    fig, ax = plt.subplots(figsize=(15, 8))
    
    monthly_data = df.groupby(['year_month', 'publisher']).size().unstack(fill_value=0)
    
    monthly_data.plot(kind='area', stacked=True, 
                     color=['#FF6B6B', '#4ECDC4'], 
                     alpha=0.8, ax=ax)
    
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Number of Articles', fontsize=12)
    ax.set_title('Monthly Article Distribution: Stacked Area Chart', 
                 fontsize=14, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    ax.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.show()


def interactive_pie_charts(df, title="Section Category Distribution Comparison"):
    """
    Create interactive side-by-side pie charts comparing section distributions.
    
    Generates two donut charts comparing NYT vs other publishers' section category
    distributions with interactive hover information.
    
    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame with 'publisher' and 'section_category' columns
    title : str, optional
        Overall title for the visualization
        
    Returns
    -------
    None
        Displays interactive plotly figure
    """
    # Compute counts for NYT vs Others
    nyt_data = df[df['publisher'] == 'New York Times']['section_category'].value_counts()
    other_data = df[df['publisher'] != 'New York Times']['section_category'].value_counts()
    
    # Create subplots
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "pie"}, {"type": "pie"}]],
        subplot_titles=("NYT Section Category Distribution", 
                       "Other Publishers Section Category Distribution")
    )
    
    # NYT pie chart
    fig.add_trace(
        go.Pie(
            labels=nyt_data.index,
            values=nyt_data.values,
            name="NYT",
            hole=0.3,
            textinfo='label+percent',
            textposition='outside',
            textfont=dict(size=12),
            hovertemplate='<b>%{label}</b><br>' +
                         'Count: %{value}<br>' +
                         'Percentage: %{percent}<br>' +
                         '<extra></extra>',
            showlegend=False
        ),
        row=1, col=1
    )
    
    # Other publishers pie chart
    fig.add_trace(
        go.Pie(
            labels=other_data.index,
            values=other_data.values,
            name="Others",
            hole=0.3,
            textinfo='label+percent',
            textposition='outside',
            textfont=dict(size=12),
            hovertemplate='<b>%{label}</b><br>' +
                         'Count: %{value}<br>' +
                         'Percentage: %{percent}<br>' +
                         '<extra></extra>',
            showlegend=False
        ),
        row=1, col=2
    )
    
    # Layout styling
    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            font=dict(size=20, family="Arial Black")
        ),
        width=1200,
        height=600,
        font=dict(size=12),
        showlegend=False
    )
    
    fig.show()


def proportional_stacked_plot(df, nyt_mask, variable, title):
    """
    Create proportional (percentage) stacked bar plots comparing NYT vs other publishers.
    
    Shows how the distribution of a categorical variable changes over time,
    normalized to percentages for easier comparison.
    
    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame with 'year' column and the specified variable
    nyt_mask : pandas.Series (bool)
        Boolean mask identifying NYT articles
    variable : str
        Column name of categorical variable to analyze
    title : str
        Title for the plots
        
    Returns
    -------
    None
        Displays matplotlib figure with two subplots
    """
    fig, axes = plt.subplots(2, 1, figsize=(15, 10), sharex=True)
    
    for ax, mask, subtitle in zip(axes, [nyt_mask, ~nyt_mask], 
                                 [f"NYT: {title}", f"Other Publishers: {title}"]):
        grouped = df[mask].groupby(["year", variable]).size().unstack(fill_value=0)
        grouped_pct = grouped.div(grouped.sum(axis=1), axis=0) * 100
        
        grouped_pct.plot(kind="bar", stacked=True, ax=ax)
        ax.set_ylabel("Percentage")
        ax.set_title(subtitle)
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    plt.tight_layout()
    plt.show()


def analyze_article_length_over_time(df):
    """
    Comprehensive analysis of article length trends over time.
    
    Performs multiple analyses:
    1. Overall statistics and yearly trends (mean, median, std dev)
    2. Distribution by decade with boxplots
    3. Publisher comparison
    
    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame with 'word_count', 'year', 'publisher' columns
        
    Returns
    -------
    None
        Prints statistics and displays visualizations
    """
    print(f"\n{'-'*60}")
    print("ARTICLE LENGTH ANALYSIS OVER TIME")
    print(f"{'-'*60}")
    
    # Filter valid articles
    df_length_analysis = df[df['word_count'] > 0].copy()
    print(f"Articles with valid word counts: {len(df_length_analysis):,} "
          f"({100*len(df_length_analysis)/len(df):.1f}%)")
    print(f"Overall average article length: {df_length_analysis['word_count'].mean():.0f} words")
    print(f"Median article length: {df_length_analysis['word_count'].median():.0f} words")
    print(f"Length range: {df_length_analysis['word_count'].min()} - "
          f"{df_length_analysis['word_count'].max():,} words")
    
    # Calculate yearly statistics
    yearly_avg_length = df_length_analysis.groupby('year')['word_count'].agg(['mean', 'median', 'std']).reset_index()
    
    # Create visualizations
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12))
    
    # 1. YEARLY TRENDS
    ax1.plot(yearly_avg_length['year'], yearly_avg_length['mean'], 
             marker='o', linewidth=2, color='darkblue', label='Mean')
    ax1.plot(yearly_avg_length['year'], yearly_avg_length['median'], 
             marker='s', linewidth=2, color='red', label='Median')
    ax1.fill_between(yearly_avg_length['year'], 
                    yearly_avg_length['mean'] - yearly_avg_length['std'],
                    yearly_avg_length['mean'] + yearly_avg_length['std'],
                    alpha=0.2, color='darkblue', label='±1 Std Dev')
    
    ax1.set_title('Average Article Length Over Time', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Year')
    ax1.set_ylabel('Average Word Count')
    ax1.legend()
    ax1.grid(alpha=0.3)
    
    # 2. BOXPLOT BY DECADE
    df_length_analysis['decade'] = (df_length_analysis['year'] // 10) * 10
    decades = sorted(df_length_analysis['decade'].unique())
    
    box_data = []
    box_labels = []
    decade_stats = []
    
    for decade in decades:
        decade_data = df_length_analysis[df_length_analysis['decade'] == decade]['word_count']
        if len(decade_data) > 0:
            box_data.append(decade_data.values)
            box_labels.append(f"{decade}s")
            decade_stats.append({
                'decade': decade,
                'count': len(decade_data),
                'median': decade_data.median(),
                'mean': decade_data.mean()
            })
    
    # Create boxplot
    bp = ax2.boxplot(box_data, labels=box_labels, patch_artist=True, 
                     showfliers=True,
                     flierprops=dict(marker='o', markerfacecolor='gray', markersize=3, alpha=0.5))
    
    # Color the boxes
    colors = ['#FF9999', '#66B2FF', '#99FF99', '#FFCC99', '#FF99CC']
    for i, patch in enumerate(bp['boxes']):
        patch.set_facecolor(colors[i % len(colors)])
        patch.set_alpha(0.7)
    
    # Add mean markers
    for i, stats in enumerate(decade_stats):
        ax2.plot(i+1, stats['mean'], marker='D', color='red', markersize=6, 
                 label='Mean' if i == 0 else "")
    
    ax2.set_title('Article Length Distribution by Decade', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Decade')
    ax2.set_ylabel('Word Count')
    ax2.grid(axis='y', alpha=0.3)
    ax2.legend()
    
    # Set y-axis limit to reduce impact of extreme outliers
    ax2.set_ylim(0, np.percentile([item for sublist in box_data for item in sublist], 95) * 1.2)
    
    plt.tight_layout()
    plt.show()
    
    # Print decade statistics
    print(f"\nDecade-by-decade breakdown:")
    for stats in decade_stats:
        print(f"  {stats['decade']}s: {stats['count']:,} articles, "
              f"median = {stats['median']:.0f} words, mean = {stats['mean']:.0f} words")
    
    # 3. PUBLISHER COMPARISON
    plt.figure(figsize=(12, 6))
    
    publishers = ['New York Times', 'Other publisher']
    colors = ['steelblue', 'darkred']
    
    for i, publisher in enumerate(publishers):
        publisher_data = df_length_analysis[df_length_analysis['publisher'] == publisher]
        if len(publisher_data) > 0:
            yearly_pub_length = publisher_data.groupby('year')['word_count'].mean()
            plt.plot(yearly_pub_length.index, yearly_pub_length.values, 
                    marker='o', linewidth=3, label=f'{publisher} ({len(publisher_data):,} articles)', 
                    color=colors[i])
    
    plt.title('Average Article Length Trends by Publisher', fontsize=14, fontweight='bold')
    plt.xlabel('Year')
    plt.ylabel('Average Word Count')
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()
    
    # Summary statistics by publisher
    print(f"\nLength comparison by publisher:")
    for publisher in publishers:
        pub_data = df_length_analysis[df_length_analysis['publisher'] == publisher]
        if len(pub_data) > 0:
            print(f"  {publisher}: {pub_data['word_count'].mean():.0f} words average, "
                  f"{pub_data['word_count'].median():.0f} words median ({len(pub_data):,} articles)")
