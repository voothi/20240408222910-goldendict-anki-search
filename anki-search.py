# anki-search.py
import argparse
import requests
import re  # Moved import here since it's only used in _strip_html


def search_word_in_decks(search_word, search_type):
    """Searches for a word in all Anki decks.

    Args:
        search_word: The word to search for.
        search_type:  The type of search to perform ("word" or "sentence").
    """

    # Anki Connect server address
    anki_connect_url = "http://localhost:8765"

    # Build the query to find card IDs
    if search_type == "word":
        # query = f'"WordSource:{search_word}"'
        # query = f'"WordSource:{search_word}" WordDestination:_*'
        query = f'"WordSource:{search_word}" (WordDestination:_* OR WordSourceMorphologyAI:_*)'
    elif search_type == "sentence":
        # query = f'"SentenceSource:*{search_word}*"'
        query = f'"SentenceSource:*{search_word}*" SentenceDestination:_*'
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
    response = requests.post(anki_connect_url, json=payload)

    # Handle the results
    if response.status_code == 200:
        result = response.json()
        card_ids = result["result"]

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
        response = requests.post(anki_connect_url, json=payload)

        if response.status_code == 200:
            result = response.json()
            card_data = []
            for card in result["result"]:
                fields = card["fields"]
                word_source = _strip_html(fields.get("WordSource", {}).get("value", ""))
                word_destination = _strip_html(fields.get("WordDestination", {}).get("value", ""))
                sentence_source = _strip_html(fields.get("SentenceSource", {}).get("value", ""))
                sentence_destination = _strip_html(fields.get("SentenceDestination", {}).get("value", ""))
                word_morphology = _strip_html(fields.get("WordSourceMorphologyAI", {}).get("value", ""))
                deck_name = card.get("deckName", None)
                card_data.append({
                    "WordSource": word_source,
                    "WordDestination": word_destination,
                    "SentenceSource": sentence_source,
                    "SentenceDestination": sentence_destination,
                    "WordSourceMorphologyAI": word_morphology,
                    "DeckName": deck_name
                })
            return card_data
        else:
            print("Error retrieving card information:", response.status_code)
            return None
    else:
        print("Error sending search query:", response.status_code)
        return None


def _strip_html(text):
    """Removes basic HTML tags from text."""
    clean = re.compile('<.*?>')
    return re.sub(clean, ' ', text)


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Search for a word in any Anki deck")
    parser.add_argument("--query", required=True, help="Word to search for in any Anki deck (e.g., --query \"test\")")
    parser.add_argument("--search-type", choices=['word', 'sentence'], default='word',
                        help="Type of search: 'word' for WordSource, 'sentence' for SentenceSource (default: word)")
    args = parser.parse_args()

    # Perform the search
    result = search_word_in_decks(args.query, args.search_type)

    # Output the results
    if result:
        for i, card in enumerate(result):
            if card['WordSource']:
                print(f"{card['WordSource']}", end='')
                if card['WordDestination']:
                    print(f" – {card['WordDestination']}")
                else:
                    print("")
            if card['SentenceSource']:
                print(f"{card['SentenceSource']}")
            if card['SentenceDestination']:
                print(f"{card['SentenceDestination']}")
            if card['WordSourceMorphologyAI']:
                print(f"{card['WordSourceMorphologyAI']}")
            if card['DeckName']:
                print(f"{card['DeckName']}")
            if i != len(result) - 1:  # Check if it's not the last record
                print("\t")  # Use tab as separator
    # else:
    #     print("Nothing found.")