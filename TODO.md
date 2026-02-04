# Project Tasks & Next Steps

## Completed Tasks
- [x] **Left Justification**: Updated CSS to left-align Samam text and ensure Rik/Mantra text is also aligned.
- [x] **Universal Samam Counting**: Implemented `samam_utils.py` and updated `generate_website.py` and `generate_granular_table.py` to use shared logic.
- [x] **CSV Metadata Sync**: Established a workflow (`src/generate_granular_table.py` -> CSV edit -> `src/generate_json.py`) to manage metadata reliably.
- [x] **Website Structure**: Implemented two-column layout and sticky navigation.
- [x] **Index Generation**: Basic indices for Rishi, Devata, Chandas are generated and linked from the homepage.

## Website Navigation & Indices
- [ ] **Refine Metadata Parsing**: Ensure `parse_metadata_str` in `generate_website.py` robustly handles all edge cases from the enriched JSON/CSV data.

## Text Quality
- [ ] **Accents & Swaras**: Continue verifying swara rendering, especially for complex combined consonants.
- [ ] **Proofreading**: Use the CSV/Excel sheet to do a sweep of Rishi/Devata/Chandas assignments.

## Future Enhancements
- [ ] **Search Functionality**: Add client-side search for verses.
- [ ] **Audio Integration**: Link audio files to individual Samams if available.
