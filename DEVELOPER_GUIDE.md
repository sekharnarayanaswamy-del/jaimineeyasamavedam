# Jaimineeya Samavedam Website Generator - Developer Guide

This project generates a static website for the Jaimineeya Samavedam, parsing a custom text format and producing a structure similar to the Rig Veda website.

## Core Components

### 1. `src/generate_website.py`
This is the main script. It contains two primary classes:

*   **`JSVParser`**: Responsible for parsing the input text file (`data/input/Samhita_...txt`). It builds a hierarchical object model of Parvas (Chapters), Kandahs (Sections), and Samas (Verses).
*   **`WebsiteGenerator`**: Takes the parsed objects and generates the HTML structure.

### 2. Output Structure (`docs/`)
The script generates the website into the `docs/` folder (configured for GitHub Pages).
*   `index.html`: The homepage with statistics and navigation.
*   `kandah/{parva_id}/{kandah_num}.html`: Individual pages for each section.
*   `css/`: Stylesheets.
*   `js/`: JavaScript files.

## Recent Features & Changes

### Layout & Navigation
*   **Layout**: The website uses a **two-column layout** (Left Sidebar + Main Content). The Right Sidebar (Jump Links) has been removed.
*   **Navigation**: All navigation is handled in the **Left Sidebar**.
    *   It lists Parvas (1-6).
    *   When a Parva is selected, it lists its Kandahs.
    *   Inside a Kandah page, it lists **Sama Ranges** (e.g., 1-5, 6-10) for quick scrolling.
*   **Samam Counting**: The script now counts verses by parsing delimiters (`||` or `॥`) inside the text, rather than just counting headers. This ensures the "Sama Count" reflects the actual chanted verses.

### Index Generation (Currently Disabled)
Code has been added to generate classification indices for **Rishi**, **Devata**, and **Chandas**, as well as an alphabetical **Header Index**.

**Status**: *Disabled/Hidden* awaiting better metadata parsing.

**Code Location**:
*   `_generate_indices()`: Method to orchestrate index creation.
*   `_collect_indices()`: Method to parse metadata strings.
*   `_generate_classification_home()`: Creates `classification/index.html`.

**How to Enable**:
1.  Open `src/generate_website.py`.
2.  Go to the `generate()` method (around line 615).
3.  Uncomment `self._generate_indices()`.
4.  Go to `_generate_homepage` and change the "Coming Soon" placeholder back to a link.

## Running the Generator

```bash
python src/generate_website.py
```

## Running a Local Server

```bash
python -m http.server 8080 --directory docs
```
Then visit: http://localhost:8080
