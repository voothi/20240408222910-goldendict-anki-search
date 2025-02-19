import argparse
import requests

def search_word_in_decks(search_word):
    # Адрес сервера Anki Connect
    anki_connect_url = "http://localhost:8765"
    
    # Формируем запрос для поиска ID карточек по полю "WordSource"
    payload = {
        "action": "findCards",
        "version": 6,
        "params": {
            "query": f'"WordSource:{search_word}"'
        }
    }
    
    # Отправляем запрос для получения ID карточек
    response = requests.post(anki_connect_url, json=payload)

    # Обрабатываем результат
    if response.status_code == 200:
        result = response.json()
        card_ids = result["result"]
        
        if not card_ids:
            # print("Ничего не найдено.")
            return None
        
        # Теперь формируем запрос для получения всей информации для каждой карточки
        payload = {
            "action": "cardsInfo",
            "version": 6,
            "params": {
                "cards": card_ids
            }
        }
        
        # Отправляем запрос для получения информации о карточках
        response = requests.post(anki_connect_url, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            # Собираем все нужные поля для каждой карточки
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
            print("Ошибка при получении информации о карточках:", response.status_code)
            return None
    else:
        print("Ошибка при отправке запроса для поиска карточек:", response.status_code)
        return None

def _strip_html(text):
    """Функция для удаления простых HTML-тегов."""
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

if __name__ == "__main__":
    # Парсинг аргументов командной строки
    parser = argparse.ArgumentParser(description="Search for a word in any Anki deck")
    parser.add_argument("search_word", help="Word to search for in any Anki deck")
    args = parser.parse_args()

    # Выполнение поиска
    result = search_word_in_decks(args.search_word)
    
    # Вывод результатов
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
            if i != len(result) - 1:  # Проверяем, не является ли текущая запись последней
                print("\t")
    else:
        print("Nothing found.")
