# Who Counts as Working Class?
## Analysis of Media Representations

**Objective:**  
This project analyzes how the working class is represented in the media. It explores changes in representation over time and compares portrayals across different publishers.

**Dataset:**  
The analysis is based on a corpus of over 40,000 articles related to the working class, published between June 1, 1980, and December 31, 2024. Sources include *The New York Times* and other major media outlets.

---

## Installation

Clone the repository:

```bash
git clone https://github.com/yourusername/working-class-media-analysis.git
cd working-class-media-analysis
```

Create and activate a virtual environment (optional but recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Usage

View the main script, `Who_is_the_Working_Class.ipynb` in a Jupyter notebook.

---

## Project Structure

```

working-class-media-analysis/
├── data/                           # Directory for raw and processed datasets
├── requirements.txt                # List of Python dependencies
├── Who_is_the_Working_Class.ipynb  # Main notebook for running the analysis
└── plots/                          # Output directory for generated plots and visualizations
└── README.md                      # Project overview and setup instructions

```

Proposed structure (discuss with Guo and Burui):

```
working-class-media-analysis/
├── data/                           # Directory for raw and processed datasets
│   ├── raw/                        # Raw, unprocessed data
│   └── processed/                  # Cleaned and structured data ready for analysis
├── data_preparation/              # Scripts or notebooks for parsing and cleaning data
│   └── prepare_data.ipynb         # Notebook/script for data parsing and cleaning
├── notebooks/                     # Main study notebooks
│   ├── Who_is_the_Working_Class.ipynb  # Study 1: Analysis of working class definitions
│   ├── Article_classification.ipynb    # Study 2: Classification of article themes/topics
│   └── POV_trends.ipynb                # Study 3: Point-of-view and discourse trends over time
├── plots/                         # Output directory for generated plots and visualizations
├── results/                       # Final outputs, e.g., tables, metrics, summaries
├── requirements.txt               # List of Python dependencies
└── README.md                      # Project overview and setup instructions
```


## Contact

TBD.
