# Release Notes

## v1.48.2 (2025-12-30)

### New Features
- **Only-IDs Mode**: Added `--only-ids` flag to retrieve only card IDs, skipping detailed data retrieval for maximum performance (1 request).
- **Optimized Single-Request Mode**: Added `--optimized` flag to leverage custom `findCardsInfo` API from `kardenwort-ankiconnect`, combining search and data retrieval into a single server-side operation.

### Improvements
- **Standard Compatibility**: Restored default lookup to use the standard 2-request method (`findCards` -> `cardsInfo`) for full compatibility with all AnkiConnect versions while maintaining TCP session reuse.
- **Search Logic Refactoring**: Unified formatting logic for default and optimized search paths.

[Return to Top](#release-notes)

---

## v1.46.12 (2025-12-29)

### Improvements
- **AnkiConnect Optimization**: Refactored API calls with helper functions for cleaner code
- **TCP Connection Reuse**: Added `requests.Session()` to reduce connection overhead
- **Better Error Messages**: Clear "[E] Anki is not running" on connection failure
- **Code Cleanup**: Removed ~40 lines of duplicate payload construction

[Return to Top](#release-notes)

---

## v1.46.2 (2025-12-29)

### New Features
- **Multi-Language Search**: Added `--languages` (alias `--lang`) argument to filter search results by language.
  - Supports short codes (e.g., `en`, `de`) which automatically expand to regional variants (e.g., `en-gb`, `en-us`).
  - Supports specific full tags (e.g., `source-de-de:1`).
- **Refined Sentence Search**: Strict mode for sentence searches ensures results have content in `SentenceDestination` fields.

### Improvements
- **Optimized Language Variants**: Removed base language codes from expansion lists to prevent Anki query parsing issues with overly broad wildcards.
- **Python 3.9 Compatibility**: Updated type hints to use `typing.Optional` and `typing.List` for compatibility with Python 3.9+.

[Return to Top](#release-notes)

