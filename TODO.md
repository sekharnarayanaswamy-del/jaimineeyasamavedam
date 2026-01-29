# Project Tasks & Next Steps

## Website Navigation & Indices
- [ ] **Refine Metadata Parsing**: The current logic for extracting Rishi, Devata, and Chandas from `rik_metadata` uses simple splitting. This needs to be improved to handle complex strings or provided with cleaner source data.
- [ ] **Enable Index Generation**: Once metadata is reliable, uncomment `self._generate_indices()` in `src/generate_website.py`.
- [ ] **Activate Homepage Link**: Change the "Coming Soon" span in `_generate_homepage` back to a clickable link pointing to `classification/index.html`.

## Code Locations
- **Parsing Logic**: `_parse_metadata` in `src/generate_website.py`
- **Index Generation**: `_generate_indices` and `_collect_indices` in `src/generate_website.py` (currently present but unused/disabled).
