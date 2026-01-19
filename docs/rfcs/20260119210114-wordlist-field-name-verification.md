20260119210114
# Wordlist Field Name Verification and Connection

## Request
Check there the field in Anki is called. Look at the project itself https://github.com/voothi/20241223170748-kardenwort

## Implementation Details

### Analytics
The user requested a "Wordlist" field output, but the exact field name in the Anki templates needs verification against the source project (Kardenwort).
Additionally, the user indicated a "connection" with a specific key (ZID `20260119210114`).

### Decisions
1.  **Field Name**: Analysis of the Kardenwort ecosystem (via [README.md](https://github.com/voothi/20241223170748-kardenwort)) reveals that the field is actually named `SentenceSourceWordlist`. 
    *   The Kardenwort runner uses the `--add-wordlist-col` flag to populate this field.
    *   The `anki-search.py` script has been updated to query `SentenceSourceWordlist` specifically.
2.  **Configuration**: The ZID `20260119210114` has been added to `config.ini` as a marker for this change.
3.  **Cross-Check**: Verified that the `--html` output mode correctly handles the `SentenceSourceWordlist` field by returning raw HTML (preserving tags), while the plain text mode uses the new `_strip_html_preserve_lines` helper to maintain the list structure.

### Changes
*   **anki-search.py**:
    *   Updated `get_val` calls in `search_word_in_decks` and `search_range_in_deck` to use `SentenceSourceWordlist` as the Anki field name.
    *   Maintained internal dictionary key as `Wordlist` for better code readability.
    *   Updated help text in `argparse` to mention `SentenceSourceWordlist`.
*   **config.ini**: Updated with ZID `20260119210114` and clarified the field name in comments.
*   **README.md**: Updated documentation to refer to the correct field name.
*   **release-notes.md**: Standardized descriptions around `SentenceSourceWordlist`.
