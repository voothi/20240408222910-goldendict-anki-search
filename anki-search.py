# anki-search.py
import argparse
import requests
import re
import pyperclip
import os
import logging
from datetime import datetime

# --- Setup Logging ---
log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'anki_search_log.txt')
logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def open_in_anki_browser(query):
    """Opens the Anki browser with a specific query."""
    logging.info(f"Attempting to open Anki Browser with query: '{query}'")
    anki_connect_url = "http://localhost:8765"
    payload = {
        "action": "guiBrowse",
        "version": 6,
        "params": {
            "query": query
        }
    }
    try:
        response = requests.post(anki_connect_url, json=payload, timeout=3)
        response.raise_for_status()
        logging.info("Successfully sent query to Anki Browser.")
        print(f"Successfully sent query to Anki Browser: {query}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending command to AnkiConnect: {e}")
        print(f"Error sending command to AnkiConnect: {e}")

def search_word_in_decks(search_word, search_type, html_output=False):
    """Searches for a word in all Anki decks."""
    # This function remains unchanged, but you could add logging here too if needed.
    anki_connect_url = "http://localhost:8765"

    if search_type == "word":
        query = f'("WordSource:*{search_word}*" OR "WordSourceInflectedForm:*{search_word}*") (WordDestination:_* OR SentenceDestination:_* OR WordSourceMorphologyAI:_*)'
    elif search_type == "sentence":
        query = f'"SentenceSource:*{search_word}*" SentenceDestination:_* WordSource:'
    else:
        raise ValueError("Invalid search_type. Must be 'word' or 'sentence'.")

    payload = { "action": "findCards", "version": 6, "params": { "query": query } }

    try:
        response = requests.post(anki_connect_url, json=payload, timeout=5)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error connecting to AnkiConnect during search: {e}")
        print(f"Error connecting to AnkiConnect: {e}")
        return None

    result = response.json()
    card_ids = result.get("result")

    if not card_ids:
        logging.info(f"No cards found for search word: '{search_word}'")
        return None

    payload = { "action": "cardsInfo", "version": 6, "params": { "cards": card_ids } }

    try:
        response = requests.post(anki_connect_url, json=payload, timeout=5)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error retrieving card info: {e}")
        print(f"Error retrieving card information: {e}")
        return None

    # ... The rest of the search function is the same ...
    result = response.json()
    card_data = []
    for card in result.get("result", []):
        fields = card.get("fields", {})

        def get_field_value(field_name):
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

def _strip_html(text):
    """Removes basic HTML tags from text."""
    clean = re.compile('<.*?>')
    text = re.sub(clean, ' ', text)
    return ' '.join(text.split())

if __name__ == "__main__":
    logging.info("Script started.")
    parser = argparse.ArgumentParser(description="Search for a word in Anki decks or open a query in the Anki Browser.")
    
    # ... Argument parsing remains the same ...
    search_group = parser.add_argument_group('Search arguments')
    search_group.add_argument("--query", help="Word to search for in any Anki deck (e.g., --query \"test\")")
    search_group.add_argument("--search-type", choices=['word', 'sentence'], default='word',
                        help="Type of search: 'word' for WordSource, 'sentence' for SentenceSource (default: word)")
    search_group.add_argument("--html", action="store_true", help="Output search results in HTML format.")
    browse_group = parser.add_argument_group('Browser arguments')
    browse_group.add_argument("--browse-query", help="A query to open directly in the Anki Browser (e.g., --browse-query \"deck:MyDeck\")")
    browse_group.add_argument("--browse-clipboard", action="store_true", help="Use the content of the clipboard as the query to open in the Anki Browser.")

    args = parser.parse_args()

    if args.browse_clipboard:
        logging.info("Mode: --browse-clipboard activated.")
        try:
            clipboard_content = pyperclip.paste()
            if clipboard_content:
                logging.info(f"Clipboard content found: '{clipboard_content[:100]}...'") # Log first 100 chars
                open_in_anki_browser(clipboard_content.strip())
            else:
                logging.warning("Clipboard is empty.")
                print("Clipboard is empty.")
        except Exception as e:
            logging.error(f"Failed to read from clipboard: {e}")
            print(f"Failed to read from clipboard: {e}")
            
    elif args.browse_query:
        logging.info(f"Mode: --browse-query activated with query: '{args.browse_query}'")
        open_in_anki_browser(args.browse_query)
        
    elif args.query:
        logging.info(f"Mode: --query activated with query: '{args.query}'")
        # ... The rest of the search logic is the same ...
        result = search_word_in_decks(args.query, args.search_type, html_output=args.html)
        if result:
            if args.html:
                for i, card in enumerate(result):
                    lines = []
                    if card['WordSource']:
                        line = f"{card['WordSource']}"
                        if card['WordDestination']:
                            line += f" – {card['WordDestination']}"
                        lines.append(line)
                    if card['WordSourceIPA']:
                        lines.append(f"[{card['WordSourceIPA']}]")
                    if card['WordSourceInflectedForm']:
                        lines.append(f"{card['WordSourceInflectedForm']}")
                    if card['SentenceSource']:
                        lines.append(f"{card['SentenceSource']}")
                    if card['SentenceDestination']:
                        lines.append(f"{card['SentenceDestination']}")
                    if card['SentenceDestination2']:
                        lines.append(f"{card['SentenceDestination2']}")
                    if card['WordSourceMorphologyAI']:
                        lines.append(f"{card['WordSourceMorphologyAI']}")
                    if card['DeckName']:
                        lines.append(f"deck:{card['DeckName']}")

                    print("<br>\n".join(lines))

                    if i < len(result) - 1:
                        print("<br><br>")
            else:
                for i, card in enumerate(result):
                    if card['WordSource']:
                        print(f"{card['WordSource']}", end='')
                        if card['WordDestination']:
                            print(f" — {card['WordDestination']}")
                        else:
                            print("")
                    if card['WordSourceIPA']:
                        print(f"[{card['WordSourceIPA']}]")
                    if card['WordSourceInflectedForm']:
                        print(f"{card['WordSourceInflectedForm']}")
                    if card['SentenceSource']:
                        print(f"{card['SentenceSource']}")
                    if card['SentenceDestination']:
                        print(f"{card['SentenceDestination']}")
                    if card['SentenceDestination2']:
                        print(f"{card['SentenceDestination2']}")
                    if card['WordSourceMorphologyAI']:
                        print(f"{card['WordSourceMorphologyAI']}")
                    if card['DeckName']:
                        print(f"deck:{card['DeckName']}")
                    if i != len(result) - 1:
                        print("\t")
    else:
        logging.info("No valid arguments provided. Printing help.")
        parser.print_help()
    
    logging.info("Script finished.")