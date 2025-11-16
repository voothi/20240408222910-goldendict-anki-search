import argparse
import requests

def get_card_ids_for_notes(note_ids):
    # Адрес сервера Anki Connect
    anki_connect_url = "http://localhost:8765"
    
    # Формируем запрос для получения идентификаторов карт для заметок
    payload = {
        "action": "notesInfo",
        "version": 6,
        "params": {
            "notes": note_ids
        }
    }
    
    # Отправляем запрос для получения информации о заметках
    response = requests.post(anki_connect_url, json=payload)
    
    # Обрабатываем результат
    if response.status_code == 200:
        result = response.json()
        card_ids = []
        for note in result["result"]:
            card_ids.extend(note["cards"])
        return card_ids
    else:
        print("Ошибка при получении идентификаторов карт для заметок:", response.status_code)
        return None

def get_decks_for_notes(note_ids):
    # Адрес сервера Anki Connect
    anki_connect_url = "http://localhost:8765"
    
    # Формируем запрос для получения названий колод для заметок
    payload = {
        "action": "getDecks",
        "version": 6,
        "params": {
            "cards": get_card_ids_for_notes(note_ids)
        }
    }
    
    # Отправляем запрос для получения названий колод
    response = requests.post(anki_connect_url, json=payload)
    
    # Обрабатываем результат
    if response.status_code == 200:
        result = response.json()
        decks = result["result"]
        return decks
    else:
        print("Ошибка при получении названий колод:", response.status_code)
        return None

def get_deck_name(note_id, decks):
    for deck_name, note_ids in decks.items():
        if note_id in note_ids:
            return deck_name
    return None  # Если ID заметки не найден в ни одной колоде, возвращаем None

def search_word_in_decks(search_word):
    # Адрес сервера Anki Connect
    anki_connect_url = "http://localhost:8765"
    
    # Формируем запрос для поиска слова в любой колоде по полю "WordSource"
    payload = {
        "action": "findNotes",
        "version": 6,
        "params": {
            "query": f"WordSource:{search_word}"
        }
    }
    
    # Отправляем запрос для получения ID заметок
    response = requests.post(anki_connect_url, json=payload)
    
    # Обрабатываем результат
    if response.status_code == 200:
        result = response.json()
        note_ids = result["result"]
        
        # Получаем названия колод для найденных заметок
        decks = get_decks_for_notes(note_ids)
        
        if decks is not None:
            # Теперь формируем запрос для получения всех полей для каждой заметки
            payload = {
                "action": "notesInfo",
                "version": 6,
                "params": {
                    "notes": note_ids
                }
            }
            
            # Отправляем запрос для получения всех полей для каждой заметки
            response = requests.post(anki_connect_url, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                # Собираем все нужные поля для каждой заметки
                note_data = []
                for note in result["result"]:
                    word_source = note["fields"].get("WordSource", {}).get("value", None)
                    word_destination = note["fields"].get("WordDestination", {}).get("value", None)
                    sentence_source = note["fields"].get("SentenceSource", {}).get("value", None)
                    card_ids = note.get("cards", [])
                    decks = get_decks_for_notes(card_ids)  # Получаем названия колод для найденных заметок
                    deck_name = get_deck_name(note["noteId"], decks)
                    note_data.append({"WordSource": word_source, "WordDestination": word_destination, "SentenceSource": sentence_source, "DeckName": deck_name})
                return note_data
            else:
                print("Ошибка при получении всех полей заметок:", response.status_code)
                return None
        else:
            print("Ошибка при получении названий колод для заметок.")
            return None
    else:
        print("Ошибка при отправке запроса для поиска заметок:", response.status_code)
        return None

if __name__ == "__main__":
    # Парсинг аргументов командной строки
    parser = argparse.ArgumentParser(description="Search for a word in any Anki deck")
    parser.add_argument("search_word", help="Word to search for in any Anki deck")
    args = parser.parse_args()

    # Выполнение поиска
    result = search_word_in_decks(args.search_word)
    
    # Вывод результатов
    if result:
        for i, note in enumerate(result):
            if note['DeckName']:
                print(f"deck:{note['DeckName']}")
            if note['WordSource']:
                print(f"{note['WordSource']}")
            if note['SentenceSource']:
                print(f"{note['SentenceSource']}")
            if note['WordDestination']:
                print(f"{note['WordDestination']}")
            if i != len(result) - 1:  # Проверяем, не является ли текущая запись последней
                print("\t")
    else:
        print("Ничего не найдено.")
