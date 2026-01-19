20260119234838

# Trailing Punctuation Fix

## Request
Why doesn’t it search at the end again with a dot, but without a dot it finds all the cards?
Why doesn’t this work, we seem to have already fixed this case?

## Analysis
The issue was in the logic for extracting the "End Anchor" for range searches.
When scanning the query backwards to find the last few words, the function `extract_anchors` was designed to stop at any "separator" (punctuation) to avoid crossing phrase boundaries.
However, if the query ended with a period (e.g., "learning."), the distinct punctuation mark was treated as a boundary immediately, resulting in a single-word anchor ("learning"). This brief anchor was often too common to effectively filter candidates, causing range search failure.
By contrast, without the dot ("learning"), the scan continued to collect preceding words ("acquisition and learning"), creating a robust anchor.

## Implementation Details
Modified `anki-search.py`:
-   Updated the `extract_anchors` function.
-   In the backward scan (End Anchor generation), added a check to ignore the "stop at separator" rule for the very first word (index 0).
-   This allows the anchor to include the final word (even if it has a trailing dot) and continue collecting preceding words to satisfy the `ANCHOR_LENGTH`.
-   This ensures that queries ending in sentences produce specific, multi-word anchors instead of single-word stubs.
