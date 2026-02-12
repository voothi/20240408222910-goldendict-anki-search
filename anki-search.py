#!/usr/bin/env python3
# anki-search.py

"""
Command-line utility to interact with Anki via the AnkiConnect add-on.

This script provides two main functionalities:
1.  Searching for cards based on complex queries and printing the results to the console
    in either plain text or HTML format.
2.  Opening the Anki card browser directly with a specified search query, which can
    be provided as an argument or taken from the system clipboard.

Requires the AnkiConnect add-on to be installed and Anki to be running.
Requires external libraries: 'requests' and 'pyperclip'.
Install them with: pip install requests pyperclip
"""

import argparse
import requests
import re
import sys
import pyperclip
import os
import configparser
from typing import Optional, List, Tuple


# AnkiConnect configuration
ANKI_CONNECT_URL = 'http://localhost:8765'
BATCH_SIZE = 100


# Configuration defaults
DEFAULT_SEPARATOR_CHARS = ". , : ; ? ! —"
DEFAULT_ANCHOR_LENGTH = 4

def load_config():
    """Load configuration from config.ini in the same directory."""
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')
    config.read(config_path)
    return config

CONFIG = load_config()
SEPARATOR_CHARS = [c.strip() for c in CONFIG.get('Search', 'separator_chars', fallback=DEFAULT_SEPARATOR_CHARS).split()]
ANCHOR_LENGTH = CONFIG.getint('Search', 'anchor_length', fallback=DEFAULT_ANCHOR_LENGTH)
VERIFY_CONTENT = CONFIG.getboolean('Search', 'verify_content', fallback=True)
ANCHOR_SOFT_MATCHING = CONFIG.getboolean('Search', 'anchor_soft_matching', fallback=True)
SHOW_WORDLIST_CONFIG = CONFIG.getboolean('Search', 'show_wordlist', fallback=False)
_deck_filter_raw = CONFIG.get('Search', 'deck_filter', fallback='').strip()
# Remove optional 'deck:' prefix if user included it
if _deck_filter_raw.lower().startswith("deck:"):
    DECK_FILTER = _deck_filter_raw[5:].strip()
else:
    DECK_FILTER = _deck_filter_raw

# Global debug flag

DEBUG = False

def debug_print(*args, **kwargs):
    """Print to stderr if DEBUG is enabled."""
    if DEBUG:
        print("[DEBUG]", *args, file=sys.stderr, **kwargs)

# Reuse TCP connection for faster sequential requests
_session = requests.Session()



def escape_anki_query(text: str) -> str:
    """
    Escapes double quotes in search text for AnkiConnect query syntax.
    
    AnkiConnect queries use double quotes to delimit field searches.
    Any literal quotes within the search term must be escaped with a backslash.
    
    Example: 'Our "formal" knowledge' -> 'Our \\"formal\\" knowledge'
    """
    return text.replace('"', '\\"')


def make_ac_request(action, **params):
    """Create AnkiConnect request payload."""
    return {'action': action, 'params': params, 'version': 6}


def parse_ac_response(response):
    """Validate and extract result from AnkiConnect response."""
    if response.get('error') is not None:
        raise Exception(response['error'])
    return response.get('result')


def invoke_ac(action, **params):
    """Execute single AnkiConnect action."""
    payload = make_ac_request(action, **params)
    try:
        response = _session.post(ANKI_CONNECT_URL, json=payload).json()
    except requests.exceptions.ConnectionError:
        print('[E] Anki is not running or AnkiConnect is not installed', file=sys.stderr)
        sys.exit(1)
    return parse_ac_response(response)


def invoke_multi_ac(actions):
    """Execute multiple AnkiConnect actions in one HTTP call."""
    results = invoke_ac('multi', actions=actions)
    return [parse_ac_response(r) for r in results]

def open_in_anki_browser(query: str):
    """
    Opens the Anki browser with a specific search query.

    This function has a side effect of opening or focusing the Anki browser window.

    Args:
        query (str): The search query string to execute in the Anki browser.
    """
    try:
        invoke_ac('guiBrowse', query=query)
        print(f"Successfully sent query to Anki Browser: {query}")
    except Exception as e:
        print(f"Error sending command to AnkiConnect: {e}")

def search_word_in_decks(search_word: str, search_type: str, languages: Optional[List[str]] = None, html_output: bool = False, only_ids: bool = False, optimized: bool = False) -> Optional[List[dict]]:
    """
    Searches for cards based on a word or sentence and returns their data.

    Args:
        search_word (str): The term to search for.
        search_type (str): The type of search, either 'word' or 'sentence'.
        languages (list[str] | None): A list of language codes to filter by (e.g., ['en', 'ru']).
                                      If None or empty, searches all languages.
        html_output (bool): If True, field values are returned with HTML tags.
                            If False, HTML tags are stripped.
        only_ids (bool): If True, only returns card IDs to speed up execution (1 request).
        optimized (bool): If True, uses the custom 'findCardsInfo' API (1 request, full data).
                          If False (default), uses standard 'findCards' + 'cardsInfo' (2 requests).

    Returns:
        A list of dictionaries, where each dictionary represents a card's data,
        or None if no cards are found or an error occurs.
    """
    anki_connect_url = "http://localhost:8765"

    # Map of short language codes to common dialect specific field suffixes.
    # This allows searching for "en" to find "en-gb", "en-us", etc.
    LANGUAGE_VARIANTS = {
        'en': ['en-gb', 'en-us'],
        'de': ['de-de'],
        'ru': ['ru-ru'],
        'uk': ['uk-ua'],
    }

    # Dynamic Condition: Language Filter (Optional)
    # If languages are specified, we add a filter to ensure the content contains the specific language tag.
    # We use a global search (no field prefix) or specific field patterns to satisfy the "not depend on field name" requirement
    # while acting as an additional filter on top of the static condition.
    # Escape search term to prevent quote-related syntax errors
    escaped_search_word = escape_anki_query(search_word)
    
    # Construct the final query.
    if search_type == "word":

        # Dynamic Condition for Words: Global/Flexible language search
        language_filter = ""
        if languages:
            conditions = []
            for lang in languages:
                if lang.startswith("source-"):
                    conditions.append(f'{lang}:_*')
                else:
                    # Expand short code to dialects if available
                    langs_to_check = LANGUAGE_VARIANTS.get(lang, [lang])
                    for variant in langs_to_check:
                         conditions.append(f'source-{variant}:_*')
            
            lang_conditions = " OR ".join(conditions)
            language_filter = f' ({lang_conditions})'

        # Static Condition for Words: Ensure at least one of the many destination fields is not empty.
        destination_check = '(WordDestination:_* OR SentenceDestination:_* OR SentenceDestination2:_* OR WordSourceMorphologyAI:_*)'
        
        # Apply Deck Filter if configured
        deck_query_part = ""
        if DECK_FILTER:
            deck_query_part = f' AND deck:"*{DECK_FILTER}*"'

        query = f'("WordSource:*{escaped_search_word}*" OR "WordSourceInflectedForm:*{escaped_search_word}*") {destination_check}{language_filter}{deck_query_part}'

    elif search_type == "sentence":
        # Dynamic Condition for Sentences: Same global/flexible language search as words
        language_filter = ""
        if languages:
            conditions = []
            for lang in languages:
                if lang.startswith("source-"):
                    conditions.append(f'{lang}:_*')
                else:
                    # Expand short code to dialects if available
                    langs_to_check = LANGUAGE_VARIANTS.get(lang, [lang])
                    for variant in langs_to_check:
                         conditions.append(f'source-{variant}:_*')

            lang_conditions = " OR ".join(conditions)
            language_filter = f' ({lang_conditions})'

        # Static Condition for Sentences: SentenceDestination OR SentenceDestination2 not empty, and WordSource empty.
        destination_check = '(SentenceDestination:_* OR SentenceDestination2:_*) WordSource:'

        # Apply Deck Filter if configured
        deck_query_part = ""
        if DECK_FILTER:
            deck_query_part = f' AND deck:"*{DECK_FILTER}*"'

        query = f'"SentenceSource:*{escaped_search_word}*" {destination_check}{language_filter}{deck_query_part}'
    else:
        raise ValueError("Invalid search_type. Must be 'word' or 'sentence'.")

    # Step 1: Find the cards (and info if not fast)
    try:
        if only_ids:
            # Fast mode: Get IDs only (1 request)
            card_ids = invoke_ac('findCards', query=query)
            if not card_ids:
                return None
            return [{"id": cid} for cid in card_ids]
        elif optimized:
             # Optimized mode: Get Card Info directly (1 request with new API)
            cards_result = invoke_ac('findCardsInfo', query=query)
            if not cards_result:
                return None
            # Optimized mode returns a list directly, ensure CardId is present or added if missing
            # Typically findCardsInfo returns objects with 'cardId'
        else:
             # Default mode: Standard compatibility (2 requests)
            card_ids = invoke_ac('findCards', query=query)
            if not card_ids:
                return None  # No cards found.

            # Step 2: Retrieve detailed information
            cards_result = invoke_ac('cardsInfo', cards=card_ids)

        # Parse and format the card data (shared for default and optimized modes)
        card_data = []
        
        # Need to normalize keys or reuse parse logic?
        # invoke_ac('cardsInfo') returns raw structure: {'fields': {'Name': {'value': '...'}}}
        # search_word_in_decks helper does flattening. We should probably reuse that logic or duplicate lightweight version.
        # Better to reuse the flattening logic if possible, or just parse directly here.
        
        for card in cards_result:
            fields = card.get("fields", {})
            
            def get_val(f, preserve_lines=False):
                 val = fields.get(f, {}).get("value", "")
                 if html_output:
                     return val
                 return _strip_html_preserve_lines(val) if preserve_lines else _strip_html(val)

            # Create standardized dict
            flat_card = {
                "CardId": card.get("cardId"),
                "WordSource": get_val("WordSource"),
                "WordSourceIPA": get_val("WordSourceIPA"),
                "WordDestination": get_val("WordDestination"),
                "SentenceSource": get_val("SentenceSource"),
                "WordSourceInflectedForm": get_val("WordSourceInflectedForm"),
                "SentenceDestination": get_val("SentenceDestination"),
                "SentenceDestination2": get_val("SentenceDestination2"),
                "WordSourceMorphologyAI": get_val("WordSourceMorphologyAI"),
                "Wordlist": get_val("SentenceSourceWordlist", preserve_lines=True),
                "DeckName": card.get("deckName", "")
            }
            card_data.append(flat_card)
            
        return card_data

    except Exception as e:
        print(f"Error communicating with AnkiConnect: {e}")
        return None


def _strip_html(text: str) -> str:
    """A simple utility to remove HTML tags from a string."""
    clean = re.compile('<.*?>')
    text = re.sub(clean, ' ', text)
    return ' '.join(text.split()) # Consolidate multiple spaces into one.

def _strip_html_preserve_lines(text: str) -> str:
    """
    Removes HTML tags but attempts to preserve line breaks from <div> and <br>.
    Useful for fields like Wordlist where structure matters.
    """
    # Replace common block/break elements with newlines
    text = re.sub(r'<(div|p|br|tr|li)[^>]*>', '\n', text, flags=re.IGNORECASE)
    # Strip remaining tags
    clean = re.compile('<.*?>')
    text = re.sub(clean, '', text)
    # Split by newline, strip, verify content, rejoin
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    return '\n'.join(lines)

# --- New Logic for Multi-Sentence/Range Search ---

def extract_anchors(query: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extracts start and end anchors from the query based on configuration.
    
    Anchors are truncated at the first/last punctuation mark to ensure they 
    do not cross phrase/card boundaries.
    """
    words = query.strip().split()
    if not words:
        return None, None

    # Helper to check for separators in a word (simple check)
    def has_separator(w):
        return any(sep in w for sep in SEPARATOR_CHARS)

    # --- Start Anchor ---
    start_anchor_words = []
    for w in words:
        if has_separator(w):
            # If word contains a separator, include it (or part of it) and stop
            # Logic: If 'hello,' we take 'hello,'. 
            # But simpler: Just take the word. The user constraint is "Stop at the first punctuation".
            # If the user meant "don't include the punctuation in the anchor search", we should strip it.
            # Usually Anki search ignores punctuation, but let's be safe and just stop *before* or include up to it.
            # Plan says: "Stop at the first punctuation... Take up to the first N words of this safe segment."
            # So if we hit a separator, we stop adding words.
            # If the FIRST word has a separator, we take just that word (or stripped?).
            # User said: "without taking over punctuation marks".
            
            # Refined Safe Logic:
            # Clean the word first? No.
            # If 'word,' -> 'word' is safe, ',' is boundary.
            # So we add 'word' and stop.
            clean_w = w
            for sep in SEPARATOR_CHARS:
                clean_w = clean_w.replace(sep, "")
            
            if clean_w:
                start_anchor_words.append(clean_w)
            break
        else:
            start_anchor_words.append(w)
            if len(start_anchor_words) >= ANCHOR_LENGTH:
                break
    
    start_anchor = " ".join(start_anchor_words)

    # --- End Anchor ---
    # Scan backwards
    end_anchor_words = []
    reversed_words = words[::-1]
    
    for i, w in enumerate(reversed_words):
        if has_separator(w):
             # Same logic as start, but backwards.
            clean_w = w
            for sep in SEPARATOR_CHARS:
                clean_w = clean_w.replace(sep, "")
            
            if clean_w:
                if i == 0:
                    end_anchor_words.append(clean_w)
                else:
                    break
            
            # If it's the very first word in the reverse scan (i.e. the last word of the query),
            # a trailing separator (like a dot) acts as the end boundary of our search, 
            # not a barrier to the words preceding it. So we continue collecting words.
            if i > 0:
                break
        else:
            end_anchor_words.append(w)
            
        if len(end_anchor_words) >= ANCHOR_LENGTH:
            break
                
    # Reverse back to normal order
    end_anchor = " ".join(end_anchor_words[::-1])

    return (start_anchor if start_anchor else None, 
            end_anchor if end_anchor else None)


def normalize_text(text: str) -> str:
    """
    Normalizes text for comparison by removing all whitespace, hyphens, HTML entities,
    and converting to lowercase. Uses logic similar to user's cleanup script.
    Reference: https://github.com/voothi/20240310195111-remove-newline-util
    """

    if not text:
        return ""
    
    # 1. Remove HTML tags (redundant if field is stripped, but safe)
    text = re.sub(r'<[^<]+?>', '', text)
    
    # 2. Remove HTML entities (e.g. &nbsp;, &amp;)
    text = re.sub(r'&\w+;', '', text)
    
    # 3. Remove hyphens (handles word breaks: "Mon-itor" -> "Monitor")
    text = text.replace('-', '')
    
    # 4. Remove all non-alphanumeric characters (includes punctuation, spaces, quotes)
    # equivalent to keeping only [a-z0-9_]
    text = re.sub(r'[^\w]', '', text)
    
    return text.lower()


def soften_anchor_query(anchor: str) -> str:
    """
    Replaces punctuation and spaces with wildcards to make Anki search lenient.
    Example: "Bellugi 1973)" -> "Bellugi*1973"
    """
    if not anchor:
        return anchor
    # Find all alphanumeric sequences and join with '*'
    words = re.findall(r'\w+', anchor)
    return "*".join(words)


def is_valid_deck(deck_name: str) -> bool:

    """
    Checks if the deck is valid for range search.
    Rule: The LEAF deck name (last part of path) must start with '0'.
    Anki decks are separated by '::'.
    """
    if not deck_name:
        return False
    # Split by separator and take the last part
    leaf_name = deck_name.split('::')[-1]
    return leaf_name.startswith('0')


def get_parent_deck(deck_name: str) -> Optional[str]:
    """
    Returns the parent deck name or None if root.
    Ex: 'Parent::Child' -> 'Parent'
    Ex: 'Root' -> None (or we could handle it, but for our logic None implies no common parent scope other than root)
    """
    if '::' not in deck_name:
        return None
    return '::'.join(deck_name.split('::')[:-1])


def reconstruct_card_text(card: dict) -> str:
    """
    Reconstructs the full text content of a card for verification.
    Concatenates SentenceSource and WordSource.
    """
    # Note: 'card' dictionary keys depend on where they came from.
    # search_word_in_decks returns keys like 'SentenceSource', 'WordSource'.
    # invoke_ac results might use 'fields' -> '...'. 
    # BUT search_word_in_decks standardizes them! 
    # Let's ensure we use the standardized keys.
    
    parts = []
    # Using .get() with default string
    ss = card.get('SentenceSource', '')
    if ss: parts.append(ss)
    
    ws = card.get('WordSource', '')
    if ws: parts.append(ws)
    
    return " ".join(parts)



def search_range_in_deck(start_card: dict, end_card: dict, original_query: str, html_output: bool = False) -> List[dict]:
    """
    Retrieves all cards in the specific deck between start_card and end_card (inclusive).
    Supports sibling decks: query will be scoped to the Common Parent Deck.
    
    Verifies that the concatenated text of the retrieved cards matches the original_query.
    """
    start_deck = start_card['DeckName']
    end_deck = end_card['DeckName']
    
    search_scope_deck = None
    
    if start_deck == end_deck:
        search_scope_deck = start_deck
    else:
        # Check if they are siblings (same parent)
        start_parent = get_parent_deck(start_deck)
        end_parent = get_parent_deck(end_deck)
        
        if start_parent and end_parent and start_parent == end_parent:
             search_scope_deck = start_parent
        else:
             # Not siblings or same deck
             return []

    # Validation: LEAF Decks start with '0'? (User constraint)
    # Both start and end LEAF decks must be valid '0-...' decks.
    if not is_valid_deck(start_deck) or not is_valid_deck(end_deck):
         return []

    min_id = min(start_card['CardId'], end_card['CardId'])
    max_id = max(start_card['CardId'], end_card['CardId'])

    debug_print(f"Search Scope Deck: '{search_scope_deck}'")
    query = f'deck:"{search_scope_deck}"'
    all_ids = invoke_ac('findCards', query=query)
    
    if not all_ids:
        return []

    
    # Filter IDs in range
    range_ids = [cid for cid in all_ids if min_id <= cid <= max_id]
    range_ids.sort()
    
    if not range_ids:
        return []
        
    # Get details
    cards_result = invoke_ac('cardsInfo', cards=range_ids)
    
    # Format
    card_data = []
    
    reconstructed_text_parts = []
    
    for card in cards_result:
        fields = card.get("fields", {})

        def get_field_value(field_name: str, strip_html: bool = True, preserve_lines: bool = False) -> str:
            value = fields.get(field_name, {}).get("value", "")
            if not strip_html:
                return value
            return _strip_html_preserve_lines(value) if preserve_lines else _strip_html(value)

        # For reconstruction, we always want stripped text
        # Preference: SentenceSource -> WordSource
        # User note: "phrase cards, that is, those whose WordSource is empty and SentenceSource is not"
        # But we should probably look at both to be safe or strictly follow the user's description.
        # Let's concatenate Sentences.
        s_source = get_field_value("SentenceSource")
        w_source = get_field_value("WordSource")
        
        # Heuristic: If SentenceSource is present, use it. Else WordSource.
        # Or construct "WordSource SentenceSource"?
        # Given the "phrase card" description, SentenceSource is the key.
        # Let's append SentenceSource if it exists.
        
        # Create a temporary flat card for reconstruction
        temp_flat_card = {
            "SentenceSource": s_source,
            "WordSource": w_source
        }
        reconstructed_text_parts.append(reconstruct_card_text(temp_flat_card))

        card_data.append({
            "CardId": card.get("cardId"),
            "WordSource": get_field_value("WordSource", strip_html=not html_output),
            "WordSourceIPA": get_field_value("WordSourceIPA", strip_html=not html_output),
            "WordDestination": get_field_value("WordDestination", strip_html=not html_output),
            "SentenceSource": get_field_value("SentenceSource", strip_html=not html_output),
            "WordSourceInflectedForm": get_field_value("WordSourceInflectedForm", strip_html=not html_output),
            "SentenceDestination": get_field_value("SentenceDestination", strip_html=not html_output),
            "SentenceDestination2": get_field_value("SentenceDestination2", strip_html=not html_output),
            "WordSourceMorphologyAI": get_field_value("WordSourceMorphologyAI", strip_html=not html_output),
            "Wordlist": get_field_value("SentenceSourceWordlist", strip_html=not html_output, preserve_lines=True),
            "DeckName": card.get("deckName", "")
        })
    
    # Verification Step
    if VERIFY_CONTENT:
        full_reconstructed_text = " ".join(reconstructed_text_parts)
        norm_query = normalize_text(original_query)
        norm_reconstructed = normalize_text(full_reconstructed_text)
        
        if norm_query not in norm_reconstructed:
            # Debug info could be useful, but for now just fail silently as per "output only if these texts match"
            # STRICT VERIFICATION: The reconstructed text MUST contain the query.
            debug_print("Verification failed.")
            debug_print(f"Query (norm): '{norm_query}'")
            debug_print(f"Found (norm): '{norm_reconstructed}'")
            return []
    else:
        debug_print("Content verification skipped (disabled in config).")


    return card_data



# --- Main execution block ---
def run_search_cli(args):
    global DEBUG
    if args.debug:
        DEBUG = True

    # Determine which action to take based on the provided arguments.

    # Priority 1: If --browse-clipboard is used, search with clipboard content.
    if args.browse_clipboard:
        import pyperclip
        clipboard_content = pyperclip.paste()
        if clipboard_content:
            open_in_anki_browser(clipboard_content.strip())
        else:
            print("Clipboard is empty.")
    # Priority 2: If a direct browse query is given.
    elif args.browse_query:
        open_in_anki_browser(args.browse_query)
    # Priority 3: If a search query is given (or via file), perform the search and print results.
    elif args.query or args.query_file:
        if args.query_file:
             try:
                 with open(args.query_file, 'r', encoding='utf-8') as f:
                     query_text = f.read().strip()
             except Exception as e:
                 print(f"Error reading query file: {e}", file=sys.stderr)
                 import sys
                 sys.exit(1)
        else:
            query_text = args.query.strip()
            
        result = None
        
        # --- Attempt Range Search if applicable ---

        # Heuristic: If query has more words than ANCHOR_LENGTH, it might be a multi-sentence/phrase segment.
        if len(query_text.split()) > ANCHOR_LENGTH:
             start_str, end_str = extract_anchors(query_text)
             debug_print(f"Anchors extracted: Start='{start_str}', End='{end_str}'")
             
             if start_str and end_str and start_str != end_str:
                 # Apply anchor softening if configured
                 if ANCHOR_SOFT_MATCHING:
                     if start_str:
                         start_str = soften_anchor_query(start_str)
                     if end_str:
                         end_str = soften_anchor_query(end_str)
                     debug_print(f"Anchors after softening: Start='{start_str}', End='{end_str}'")

                 # Search for Start Cards
                 start_candidates = search_word_in_decks(start_str, args.search_type, languages=args.languages, html_output=args.html, optimized=args.optimized)
                 debug_print(f"Start candidates found: {len(start_candidates) if start_candidates else 0}")
                 if start_candidates:
                      for cand in start_candidates:
                          debug_print(f"Start Candidate: ID={cand.get('CardId')}, Deck='{cand.get('DeckName')}'")

                 
                 # Search for End Cards
                 end_candidates = search_word_in_decks(end_str, args.search_type, languages=args.languages, html_output=args.html, optimized=args.optimized)
                 debug_print(f"End candidates found: {len(end_candidates) if end_candidates else 0}")
                 if start_candidates and end_candidates:
                     # Find a matching pair in the same deck (starting with 0)
                     found_range = False
                     for s_card in start_candidates:
                         if found_range: break
                         
                         # Check deck prefix constraint early
                         if not is_valid_deck(s_card['DeckName']):
                             debug_print(f"Skipping Start Candidate (Leaf Deck not '0...'): Deck='{s_card['DeckName']}'")
                             continue

                         for e_card in end_candidates:
                             # Logic update: Allow same deck OR sibling decks (same parent)
                             is_sibling = False
                             if s_card['DeckName'] != e_card['DeckName']:
                                 # Check if siblings
                                 s_parent = get_parent_deck(s_card['DeckName'])
                                 e_parent = get_parent_deck(e_card['DeckName'])
                                 if not (s_parent and e_parent and s_parent == e_parent):
                                     # debug_print(f"Skipping End Candidate (Deck mismatch/Not siblings): StartDeck='{s_card['DeckName']}', EndDeck='{e_card['DeckName']}'")
                                     continue
                                 
                             if s_card['CardId'] > e_card['CardId']:
                                 debug_print(f"Skipping End Candidate (ID Order): StartID={s_card['CardId']}, EndID={e_card['CardId']}")
                                 continue

                             # OPTIMIZATION: Single Card Match?
                             if s_card['CardId'] == e_card['CardId']:
                                 debug_print(f"Single card candidate found (ID={s_card['CardId']}). Verifying locally...")
                                 # Reconstruct and Verify
                                 if VERIFY_CONTENT:
                                     card_text = reconstruct_card_text(s_card)
                                     if normalize_text(query_text) in normalize_text(card_text):
                                          debug_print("Single card range verified and accepted.")
                                          result = [s_card]
                                          found_range = True
                                          break
                                     else:
                                          debug_print("Single card content mismatch.")
                                          continue
                                 else:
                                     debug_print("Single card range accepted (verification skipped).")
                                     result = [s_card]
                                     found_range = True
                                     break


                             # Found a valid range!
                             debug_print(f"Checking candidate range: Deck='{s_card['DeckName']}', StartID={s_card['CardId']}, EndID={e_card['CardId']}")

                             range_result = search_range_in_deck(s_card, e_card, query_text, html_output=args.html)
                             if range_result:
                                 debug_print("Range verified and accepted.")
                                 result = range_result
                                 found_range = True
                                 break

                     if not found_range:
                         debug_print("No valid verified range found among candidates.")
        
        # --- Fallback to Standard Search ---
        if not result:
             debug_print("Falling back to standard search.")
             result = search_word_in_decks(query_text, args.search_type, languages=args.languages, html_output=args.html, only_ids=args.only_ids, optimized=args.optimized)

        if result:
            show_wordlist = args.show_wordlist or SHOW_WORDLIST_CONFIG
            
            if args.only_ids:
                 # Fast mode output: just IDs
                 print(f"Found {len(result)} cards:")
                 for card in result:
                     print(f"ID: {card['id']}")
            else:
                # Format and print the results based on whether HTML output is requested.
                if args.html:
                    for i, card in enumerate(result):
                        lines = []
                        if card['WordSourceIPA']: lines.append(f"[{card['WordSourceIPA']}]")
                        if card['WordSource']:
                            line = f"{card['WordSource']}"
                            if card['WordDestination']:
                                line += f" - {card['WordDestination']}"
                            lines.append(line)
                        if card['WordSourceInflectedForm']: lines.append(f"{card['WordSourceInflectedForm']}")
                        if card['SentenceSource']: lines.append(f"{card['SentenceSource']}")
                        if card['SentenceDestination']: lines.append(f"- {card['SentenceDestination']}")
                        if card['SentenceDestination2']: lines.append(f"- {card['SentenceDestination2']}")
                        if card['WordSourceMorphologyAI']: lines.append(f"{card['WordSourceMorphologyAI']}")
                        if show_wordlist and card.get('Wordlist'): lines.append(f"{card['Wordlist']}")
                        if card['DeckName']: lines.append(f"deck:{card['DeckName']}")

                        print("<br>\n".join(lines))

                        # Add a separator between cards.
                        if i < len(result) - 1:
                            print("<br><br>")
                else: # Plain text output
                    for i, card in enumerate(result):
                        if card['WordSourceIPA']: print(f"[{card['WordSourceIPA']}]")
                        if card['WordSource']:
                            print(f"{card['WordSource']}", end='')
                            if card['WordDestination']:
                                print(f" - {card['WordDestination']}")
                            else:
                                print("")
                        if card['WordSourceInflectedForm']: print(f"{card['WordSourceInflectedForm']}")
                        if card['SentenceSource']: print(f"{card['SentenceSource']}")
                        if card['SentenceDestination']: print(f"- {card['SentenceDestination']}")
                        if card['SentenceDestination2']: print(f"- {card['SentenceDestination2']}")
                        if card['WordSourceMorphologyAI']: print(f"{card['WordSourceMorphologyAI']}")
                        if show_wordlist and card.get('Wordlist'): print(f"{card['Wordlist']}")
                        if card['DeckName']: print(f"deck:{card['DeckName']}")
                        
                        # Add a separator between cards.
                        if i != len(result) - 1:
                            print("\t")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Search for a word in Anki decks or open a query in the Anki Browser.")
    search_group = parser.add_argument_group('Search arguments')
    search_group.add_argument("--query", help="Word to search for in any Anki deck (e.g., --query \"test\")")
    search_group.add_argument("--search-type", choices=['word', 'sentence'], default='word',
                        help="Type of search: 'word' for WordSource, 'sentence' for SentenceSource (default: word)")
    search_group.add_argument("--languages", "--lang", nargs='*',
                        help="List of languages to filter by (e.g., --languages en source-de-de:1). Filters based on 'source-{lang}-' tag or exact match if starting with 'source-'.")
    search_group.add_argument("--show-wordlist", action="store_true", help="Display the 'SentenceSourceWordlist' field in the output.")
    search_group.add_argument("--html", action="store_true", help="Output search results in HTML format.")
    search_group.add_argument("--only-ids", action="store_true", help="Fast mode: only check for existence (returns IDs), skipping detailed info.")
    search_group.add_argument("--optimized", action="store_true", help="Use the optimized 'findCardsInfo' API (requires kardenwort-ankiconnect).")
    search_group.add_argument("--debug", action="store_true", help="Enable debug output to stderr.")
    search_group.add_argument("--query-file", help="Read query from a file (overrides --query).")
    browse_group = parser.add_argument_group('Browser arguments')
    browse_group.add_argument("--browse-query", help="A query to open directly in the Anki Browser (e.g., --browse-query \"deck:MyDeck\")")
    browse_group.add_argument("--browse-clipboard", action="store_true", help="Use the content of the clipboard as the query to open in the Anki Browser.")
    args = parser.parse_args()
    if args.query or args.query_file or args.browse_clipboard or args.browse_query:
        run_search_cli(args)
    else:
        parser.print_help()
