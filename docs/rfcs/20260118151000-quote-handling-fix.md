# Robust Quote Handling in Search Queries

## ZID
20260118151000

## Related ZIDs
- 20260118144843 (Initial issue report)
- 20260118150034 (Request for tests)

## Implementation Details

This change addresses a critical failure in AnkiConnect search queries when the selected source text contains double quotation marks, particularly at the beginning of the selection.

### Problem Analysis
AnkiConnect's `findCards` and `findCardsInfo` actions use a search syntax where field-specific lookups are encapsulated in double quotes. For example:
`"SentenceSource:*Our \"formal\" knowledge*"`

If the search term itself contains literal double quotes (e.g., `Our "formal" knowledge`), and these are not escaped, the resulting query becomes syntactically invalid for Anki's search engine, leading to zero results or errors.

### Technical Solution
We implemented a dedicated escaping layer to sanitize all search terms before they are injected into the query templates.

1.  **Escaping Logic**: A new helper function `escape_anki_query(text)` was introduced. It explicitly converts all literal double quotes (`"`) into backslash-escaped quotes (`\"`).
2.  **Unified Application**: This transformation is applied to the `search_word` at the start of `search_word_in_decks`, ensuring that both standard lookups and anchor-based range searches benefit from the improved robustness.
3.  **Range Search Integration**: Since range search relies on finding "Start" and "End" anchors (which are substrings of the original query), the escaping ensures that these anchors can be successfully matched even if they contain punctuation or quotes.

### Verification and Testing
To prevent regressions, we added a suite of automated tests:
- **Unit Testing**: Verified `escape_anki_query` correctly handles quotes at the start, middle, and end of strings.
- **Mock Integration Testing**: Captured the calls to `invoke_ac` to verify that the final query string sent to Anki contains the expected `\"` sequences for both `word` and `sentence` search types.
