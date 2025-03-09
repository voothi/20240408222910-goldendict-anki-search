# anki-search.py
import argparse
import requests

def search_word_in_decks(search_word):
    """Searches for a word in all Anki decks."""

    # Anki Connect server address
    anki_connect_url = "http://localhost:8765"

    # Build the query to find card IDs based on the "WordSource" field
    payload = {
        "action": "findCards",
        "version": 6,
        "params": {
            # "query": f'"WordSource:{search_word}"'  # Use double quotes to correctly handle the colon
            "query": f'"SentenceSource:*{search_word}*"'  # Use double quotes to correctly handle the colon
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
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, ' ', text)

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Search for a word in any Anki deck")
    parser.add_argument("--query", required=True, help="Word to search for in any Anki deck (e.g., --query \"test\")")  # Changed to --query and made required
    args = parser.parse_args()

    # Perform the search
    result = search_word_in_decks(args.query)

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
                print("\t") #Use tab as separator 
    else:
        print("Nothing found.")
