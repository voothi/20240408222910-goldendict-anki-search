# Release Notes

## v1.50.2 (2026-01-17)

### New Features
- **Multi-Sentence Range Search**: Automatically detects long technical queries spanning multiple cards.
  - Identifies start and end anchors to define the search range.
  - Reconstructs and verifies full text content using aggressive normalization.
  - Supports searching across sibling decks (common parent scope).
- **Configuration Support**: Added `config.ini` for customizable settings:
  - `anchor_length`: Number of words used for boundary detection (default: 4).
  - `separator_chars`: List of punctuation marks that define anchor boundaries.
  - `verify_content`: Toggle strict identity check (useful for AI-processed text).

- **Improved Arguments**:
  - `--debug`: Prints detailed execution trace to `stderr`.
  - `--query-file`: Allows reading long queries from a UTF-8 file to avoid shell character limits.

### Improvements
- **Single-Card Optimization**: Short-circuits the range search logic if start and end anchors match the same card, reducing API latency.
- **Robust Verification**: Changed content verification to substring matching, allowing successful results for partial user selections.
- **Leaf Deck Validation**: Range search restricted to decks where the leaf name starts with '0'.

[Return to Top](#release-notes)

---

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

