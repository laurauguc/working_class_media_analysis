# 📂 Data Processing

This folder contains scripts and documentation for transforming raw `.DOCX` article files into structured, analyzable data. The pipeline is organized into two main stages:

1. **Parsing** – Extracting article metadata and content from `.DOCX` files  
2. **Data Cleaning** – Normalizing and filtering the parsed data

---

## 🧩 1. Parsing

### 📄 Script

[`1.parse_articles.py`](./1.parse_articles.py)

### 📝 Description

This script reads `.DOCX` files from the `../data/raw/` directory and extracts structured information from each article.

Each extracted article includes the following fields:
- `title`
- `publisher`
- `date` (with special handling for entries like `Correction Appended` and `Load-Date`)
- `section`
- `length`
- `body`
- Flags:
  - `correction_appended`
  - `load_date_at_end`
- `source_file` – Relative path for traceability

Articles are identified based on paragraphs styled as `Heading 1`.

### ▶️ Usage

Run the script with optional flags:

```bash
python parse_articles.py --save-intermediate
```

**Flag:**  
`--save-intermediate` — Saves individual parsed articles as `.pkl` files in `../data/processed/parsed_files/` (useful for debugging or inspecting progress).

💡 **Tip:** To prevent your computer from sleeping during long runs, use `caffeinate`:

```bash
caffeinate python parse_articles.py --save-intermediate
```

### 📥 Input

A collection of `.DOCX` files located in:  `../data/raw/`.

### 📦 Output

Combined parsed articles:

```bash
../data/processed/parsed_articles.pkl
```

## 🧼 2. Data Cleaning

### 📄 Script

[`2.clean_data.ipynb`](2.clean_data.ipynb)


### 📝 Description

This step transforms the parsed data into a clean, analysis-ready format by performing:

(to complete)

### ▶️ Usage

(to complete)

### 📥 Input

`../data/processed/parsed_articles.pkl`

### 📦 Output

`../data/processed/cleaned_articles.pkl`

## ✅ To-Do

- [ ] Review `clean_data.py`
- [ ] Discuss observation with team and finalize script
- [ ] Finalize data processing documentation
- [ ] Delete extra files in this folder (0. Coding practices.ipynb, 3. Data checks.ipynb)
