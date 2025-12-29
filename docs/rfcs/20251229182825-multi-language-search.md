# Multi-Language Search Support

**ZID**: 20251229182825
**Status**: Implemented
**Date**: 2025-12-29

## Context
The user needed a way to invoke `anki-search.py` with a language filter to narrow down search results to specific languages. This is particularly important for polyglot decks or when searching potential "false friend" words that exist in multiple languages (e.g., searching for a German word shouldn't return English cards).

## Implementation Details
1.  **New Argument**: Added `--languages` (and alias `--lang`) to the command-line arguments. It accepts a list of language codes (e.g., `en`, `de`) or full tags (e.g., `source-de-de:1`).
2.  **Language Variant Expansion**:
    - Implemented a `LANGUAGE_VARIANTS` dictionary to automatically expand short codes into their common regional variants.
    - Example: `en` expands to `en`, `en-gb`, `en-us`, `en-au`, `en-ca`.
    - This ensures that searching for "en" catches all specific English tags.
3.  **Search Logic**:
    - **Word Search**: Applies a flexible global language filter `(*source-{lang}*:_*)` combined with a check that at least one destination field is not empty.
    - **Sentence Search**: Applies the same global language filter (to catch the tag wherever it is on the card) but imposes a strict check on `SentenceDestination` or `SentenceDestination2` being not empty `(SentenceDestination:_* OR SentenceDestination2:_*)` to ensure it is a valid sentence card.
    - The language filter uses the `AND` operator with the main query, and `OR` between multiple specified languages.
4.  **Syntax**:
    - Used `*source-{lang}*:_*` pattern for finding language tags. This checks for the existence of a field matching the pattern that is non-empty.
    - Used `*{tag}*:_*` for specific full tags provided by the user.

## Decision Log
- **Field Agnostic**: The language filter does not hardcode which field contains the language tag (except for relying on the naming convention `source-...`). This allows flexibility if the tag is in `WordDestination` or `SentenceSource`.
- **Strict Sentence Mode**: Initially, the query was too broad for sentences. We narrowed the *static check* to `SentenceDestination` fields, but kept the *language filter* global to ensure we find the language tag even if it sits in a different field on the same card logic.
