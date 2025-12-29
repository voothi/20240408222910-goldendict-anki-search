# Release Notes

## v1.46.2 (2025-12-29)

### New Features
- **Multi-Language Search**: Added `--languages` (alias `--lang`) argument to filter search results by language.
  - Supports short codes (e.g., `en`, `de`) which automatically expand to regional variants (e.g., `en-gb`, `en-us`).
  - Supports specific full tags (e.g., `source-de-de:1`).
- **Refined Sentence Search**: strict mode for sentence searches ensures results have content in `SentenceDestination` fields.
