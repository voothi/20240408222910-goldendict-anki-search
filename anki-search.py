# anki-search.py
import argparse
import requests
import re


def search_word_in_decks(search_word, search_type, html_output=False):
    """Searches for a word in all Anki decks.

    Args:
        search_word: The word to search for.
        search_type:  The type of search to perform ("word" or "sentence").
        html_output: If True, do not strip HTML tags from the output.
    """

    # Anki Connect server address
    anki_connect_url = "http://localhost:8765"

    # Build the query to find card IDs
    if search_type == "word":
        query = f'"WordSource:{search_word}" (WordDestination:_* OR SentenceDestination:_* OR WordSourceMorphologyAI:_*)'
    elif search_type == "sentence":
        query = f'"SentenceSource:*{search_word}*" SentenceDestination:_* WordSource:'
    else:
        raise ValueError("Invalid search_type. Must be 'word' or 'sentence'.")

    payload = {
        "action": "findCards",
        "version": 6,
        "params": {
            "query": query
        }
    }

    # Send the request to get card IDs
    try:
        response = requests.post(anki_connect_url, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to AnkiConnect: {e}")
        return None

    # Handle the results
    result = response.json()
    card_ids = result.get("result")

    if not card_ids:
        return None  # No cards found

    # Build the query to get card information
    payload = {
        "action": "cardsInfo",
        "version": 6,
        "params": {
            "cards": card_ids
        }
    }

    # Send the request to get card information
    try:
        response = requests.post(anki_connect_url, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving card information: {e}")
        return None

    result = response.json()
    card_data = []
    for card in result.get("result", []):
        fields = card.get("fields", {})

        def get_field_value(field_name):
            """Gets a field's value, optionally stripping HTML."""
            value = fields.get(field_name, {}).get("value", "")
            return value if html_output else _strip_html(value)

        card_data.append({
            "WordSource": get_field_value("WordSource"),
            "WordSourceIPA": get_field_value("WordSourceIPA"),
            "WordDestination": get_field_value("WordDestination"),
            "SentenceSource": get_field_value("SentenceSource"),
            "SentenceDestination": get_field_value("SentenceDestination"),
            "SentenceDestination2": get_field_value("SentenceDestination2"),
            "WordSourceMorphologyAI": get_field_value("WordSourceMorphologyAI"),
            "DeckName": card.get("deckName", "")
        })
    return card_data


def _strip_html(text):
    """Removes basic HTML tags from text."""
    clean = re.compile('<.*?>')
    # Replace tags with a space and then clean up multiple spaces
    text = re.sub(clean, ' ', text)
    return ' '.join(text.split())


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Search for a word in any Anki deck")
    parser.add_argument("--query", required=True, help="Word to search for in any Anki deck (e.g., --query \"test\")")
    parser.add_argument("--search-type", choices=['word', 'sentence'], default='word',
                        help="Type of search: 'word' for WordSource, 'sentence' for SentenceSource (default: word)")
    parser.add_argument("--html", action="store_true", help="Output results in HTML format with line breaks.")
    args = parser.parse_args()

    # Perform the search, passing the html flag
    result = search_word_in_decks(args.query, args.search_type, html_output=args.html)

    # Output the results
    if result:
        if args.html:
            # --- HTML Output Mode ---
            for i, card in enumerate(result):
                lines = []
                if card['WordSource']:
                    line = f"{card['WordSource']}"
                    if card['WordDestination']:
                        line += f" – {card['WordDestination']}"
                    lines.append(line)
                if card['WordSourceIPA']:
                    lines.append(f"[{card['WordSourceIPA']}]")
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

                if i < len(result) - 1:  # Add a separator between cards
                    print("<br><br>")
        else:
            # --- Plain Text Output Mode (Original) ---
            for i, card in enumerate(result):
                if card['WordSource']:
                    print(f"{card['WordSource']}", end='')
                    if card['WordDestination']:
                        print(f" — {card['WordDestination']}")
                    else:
                        print("")
                if card['WordSourceIPA']:
                    print(f"[{card['WordSourceIPA']}]")
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
                if i != len(result) - 1:  # Check if it's not the last record
                    print("\t")
    # else:
    #     print("Nothing found.")