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
import pyperclip

def open_in_anki_browser(query: str):
    """
    Opens the Anki browser with a specific search query.

    This function has a side effect of opening or focusing the Anki browser window.

    Args:
        query (str): The search query string to execute in the Anki browser.
    """
    anki_connect_url = "http://localhost:8765"
    # Construct the JSON-RPC payload for the 'guiBrowse' action.
    payload = {
        "action": "guiBrowse",
        "version": 6,
        "params": {
            "query": query
        }
    }
    try:
        response = requests.post(anki_connect_url, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx).
        print(f"Successfully sent query to Anki Browser: {query}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending command to AnkiConnect: {e}")

def search_word_in_decks(search_word: str, search_type: str, languages: list[str] | None = None, html_output: bool = False) -> list[dict] | None:
    """
    Searches for cards based on a word or sentence and returns their data.

    Args:
        search_word (str): The term to search for.
        search_type (str): The type of search, either 'word' or 'sentence'.
        languages (list[str] | None): A list of language codes to filter by (e.g., ['en', 'ru']).
                                      If None or empty, searches all languages.
        html_output (bool): If True, field values are returned with HTML tags.
                            If False, HTML tags are stripped.

    Returns:
        A list of dictionaries, where each dictionary represents a card's data,
        or None if no cards are found or an error occurs.
    """
    anki_connect_url = "http://localhost:8765"

    # Dynamic Condition: Language Filter (Optional)
    # If languages are specified, we add a filter to ensure the content contains the specific language tag.
    # We use a global search (no field prefix) or specific field patterns to satisfy the "not depend on field name" requirement
    # while acting as an additional filter on top of the static condition.
    # Construct the final query.
    if search_type == "word":
        # Dynamic Condition for Words: Global/Flexible language search (User preferred syntax)
        language_filter = ""
        if languages:
            conditions = []
            for lang in languages:
                if lang.startswith("source-"):
                    conditions.append(f'*{lang}*')
                else:
                    conditions.append(f'*source-{lang}-*:_*')
            lang_conditions = " OR ".join(conditions)
            language_filter = f' ({lang_conditions})'

        # Static Condition for Words: Ensure at least one of the many destination fields is not empty.
        destination_check = '(WordDestination:_* OR SentenceDestination:_* OR SentenceDestination2:_* OR WordSourceMorphologyAI:_*)'
        query = f'("WordSource:*{search_word}*" OR "WordSourceInflectedForm:*{search_word}*") {destination_check}{language_filter}'

    elif search_type == "sentence":
        # Dynamic Condition for Sentences: Strict Check on SentenceDestination
        # Prevents false positives where 'WordDestination' matches the language but 'SentenceDestination' does not.
        language_filter = ""
        if languages:
            conditions = []
            for lang in languages:
                # If full tag provided, assume it applies to SentenceDestination if it's a value search
                if lang.startswith("source-"):
                     conditions.append(f'SentenceDestination:*{lang}*')
                else:
                     conditions.append(f'SentenceDestination:*source-{lang}-*')
            lang_conditions = " OR ".join(conditions)
            language_filter = f' ({lang_conditions})'

        # Static Condition for Sentences: Strict check on SentenceDestination being present and WordSource being empty.
        destination_check = 'SentenceDestination:_* WordSource:'
        query = f'"SentenceSource:*{search_word}*" {destination_check}{language_filter}'
    else:
        raise ValueError("Invalid search_type. Must be 'word' or 'sentence'.")

    # Step 1: Find the IDs of cards matching the query.
    payload = {
        "action": "findCards",
        "version": 6,
        "params": { "query": query }
    }
    try:
        response = requests.post(anki_connect_url, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to AnkiConnect: {e}")
        return None

    card_ids = response.json().get("result")
    if not card_ids:
        return None # No cards found.

    # Step 2: Retrieve detailed information for the found card IDs.
    payload = {
        "action": "cardsInfo",
        "version": 6,
        "params": { "cards": card_ids }
    }
    try:
        response = requests.post(anki_connect_url, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving card information: {e}")
        return None

    # Step 3: Parse and format the card data.
    card_data = []
    for card in response.json().get("result", []):
        fields = card.get("fields", {})

        def get_field_value(field_name: str) -> str:
            """Helper to safely extract field values and optionally strip HTML."""
            value = fields.get(field_name, {}).get("value", "")
            return value if html_output else _strip_html(value)

        card_data.append({
            "WordSource": get_field_value("WordSource"),
            "WordSourceIPA": get_field_value("WordSourceIPA"),
            "WordDestination": get_field_value("WordDestination"),
            "SentenceSource": get_field_value("SentenceSource"),
            "WordSourceInflectedForm": get_field_value("WordSourceInflectedForm"),
            "SentenceDestination": get_field_value("SentenceDestination"),
            "SentenceDestination2": get_field_value("SentenceDestination2"),
            "WordSourceMorphologyAI": get_field_value("WordSourceMorphologyAI"),
            "DeckName": card.get("deckName", "")
        })
    return card_data

def _strip_html(text: str) -> str:
    """A simple utility to remove HTML tags from a string."""
    clean = re.compile('<.*?>')
    text = re.sub(clean, ' ', text)
    return ' '.join(text.split()) # Consolidate multiple spaces into one.

# --- Main execution block ---
if __name__ == "__main__":
    # Set up the command-line argument parser.
    parser = argparse.ArgumentParser(description="Search for a word in Anki decks or open a query in the Anki Browser.")
    
    # Group arguments for clarity: one for searching, one for opening the browser.
    search_group = parser.add_argument_group('Search arguments')
    search_group.add_argument("--query", help="Word to search for in any Anki deck (e.g., --query \"test\")")
    search_group.add_argument("--search-type", choices=['word', 'sentence'], default='word',
                        help="Type of search: 'word' for WordSource, 'sentence' for SentenceSource (default: word)")
    search_group.add_argument("--languages", "--lang", nargs='*',
                        help="List of languages to filter by (e.g., --languages en source-de-de:1). Filters based on 'source-{lang}-' tag or exact match if starting with 'source-'.")
    search_group.add_argument("--html", action="store_true", help="Output search results in HTML format.")

    browse_group = parser.add_argument_group('Browser arguments')
    browse_group.add_argument("--browse-query", help="A query to open directly in the Anki Browser (e.g., --browse-query \"deck:MyDeck\")")
    browse_group.add_argument("--browse-clipboard", action="store_true", help="Use the content of the clipboard as the query to open in the Anki Browser.")

    args = parser.parse_args()

    # Determine which action to take based on the provided arguments.
    # Priority 1: If --browse-clipboard is used, search with clipboard content.
    if args.browse_clipboard:
        clipboard_content = pyperclip.paste()
        if clipboard_content:
            open_in_anki_browser(clipboard_content.strip())
        else:
            print("Clipboard is empty.")
    # Priority 2: If a direct browse query is given.
    elif args.browse_query:
        open_in_anki_browser(args.browse_query)
    # Priority 3: If a search query is given, perform the search and print results.
    elif args.query:
        result = search_word_in_decks(args.query, args.search_type, languages=args.languages, html_output=args.html)
        if result:
            # Format and print the results based on whether HTML output is requested.
            if args.html:
                for i, card in enumerate(result):
                    lines = []
                    if card['WordSource']:
                        line = f"{card['WordSource']}"
                        if card['WordDestination']:
                            line += f" - {card['WordDestination']}"
                        lines.append(line)
                    # Add other fields if they exist
                    if card['WordSourceIPA']: lines.append(f"[{card['WordSourceIPA']}]")
                    if card['WordSourceInflectedForm']: lines.append(f"{card['WordSourceInflectedForm']}")
                    if card['SentenceSource']: lines.append(f"{card['SentenceSource']}")
                    if card['SentenceDestination']: lines.append(f"- {card['SentenceDestination']}")
                    if card['SentenceDestination2']: lines.append(f"- {card['SentenceDestination2']}")
                    if card['WordSourceMorphologyAI']: lines.append(f"{card['WordSourceMorphologyAI']}")
                    if card['DeckName']: lines.append(f"deck:{card['DeckName']}")

                    print("<br>\n".join(lines))

                    # Add a separator between cards.
                    if i < len(result) - 1:
                        print("<br><br>")
            else: # Plain text output
                for i, card in enumerate(result):
                    if card['WordSource']:
                        print(f"{card['WordSource']}", end='')
                        if card['WordDestination']:
                            print(f" — {card['WordDestination']}")
                        else:
                            print("")
                    if card['WordSourceIPA']: print(f"[{card['WordSourceIPA']}]")
                    if card['WordSourceInflectedForm']: print(f"{card['WordSourceInflectedForm']}")
                    if card['SentenceSource']: print(f"{card['SentenceSource']}")
                    if card['SentenceDestination']: print(f"- {card['SentenceDestination']}")
                    if card['SentenceDestination2']: print(f"- {card['SentenceDestination2']}")
                    if card['WordSourceMorphologyAI']: print(f"{card['WordSourceMorphologyAI']}")
                    if card['DeckName']: print(f"deck:{card['DeckName']}")
                    
                    # Add a separator between cards.
                    if i != len(result) - 1:
                        print("\t")
    # If no valid arguments are provided, show the help message.
    else:
        parser.print_help()