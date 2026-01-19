
## v1.52.12 (2026-01-19)

### Bug Fixes
- **Trailing Punctuation**: Fixed an issue where searches ending with a period (e.g., "... learning.") often failed.
  - The script now correctly includes preceding words in the search anchor even if the selection ends with punctuation, ensuring a robust and specific search query.
  - Previously, trailing punctuation caused the search anchor to be truncated to a single word.

## v1.52.10 (2026-01-19)

### New Features
- **Wordlist Field Support**: Added option to display the content of the `SentenceSourceWordlist` field in search results.
  - Disabled by default. Can be enabled via `config.ini` (`show_wordlist = true`) or command-line flag (`--show-wordlist`).
  - Output is formatted line-by-line, preserving the structure of the list from Anki (e.g., maintaining `<div>` or `<br>` breaks).

### Improvements
- **Detailed Testing**: Added unit tests covering HTML structure preservation and Wordlist field retrieval.

## v1.52.8 (2026-01-18)

### New Features
- **Lenient Anchor Search**: Added `anchor_soft_matching` to handle punctuation differences in paragraph reading mode.
  - Automatically replaces spaces and punctuation in search anchors with wildcards (`*`).
  - Successfully matches cards even when the database contains extra punctuation (e.g., trailing commas, semicolons) that is not in the search query.
  - Configurable via `config.ini` (default: `true`).

### Improvements
- **Standardized Search Logic**: The `anchor_soft_matching` feature now effectively ignores and bypasses any punctuation like `;`, `,`, `.`, `!`, `?`, `(`, and `)` during the initial lookup in Anki, significantly improving the success rate of paragraph-range searches.
- **Diagnostics**: Enhanced `--debug` output to show the state of softened anchors.

## v1.52.6 (2026-01-18)

### Bug Fixes
- **Quote Handling**: Fixed a critical issue where search queries containing double quotes (especially at the beginning of selected text) caused AnkiConnect queries to fail.
- **Improved Escaping**: Implemented internal `escape_anki_query` logic to properly handle literal quotation marks within search terms, ensuring compatibility with Anki's query parser.
- **Robustness**: Enhanced reliability for multi-sentence range searches and individual word lookups when the source text includes punctuation or quotes.

## v1.52.4 (2026-01-18)

### Improvements
-   **Field Reordering**: Swapped the display order of `IPA` and `WordSource` in search results. `IPA` is now displayed first.
-   **Lemma Comparison**: This change aligns with [Kardenwort Anki Templates](https://github.com/voothi/20241106211123-kardenwort-anki-templates) to facilitate side-by-side comparison of the lemma and the original word.
-   **Standardized Separator**: Changed the separator in plain text output from an em-dash (`—`) to a hyphen (`-`) for consistency.

## v1.52.2 (2026-01-17)

### New Features
- **Deck Filtering**: Added `deck_filter` key to `config.ini` to limit valid search results to a specific deck or hierarchy.
  - Supports wildcard matching for unique IDs (e.g., `201100` matches `Root::201100-MyDeck`).
  - Supports optional `deck:` prefix for easier pasting.
  - Supports multi-line indented values for long deck names.

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

