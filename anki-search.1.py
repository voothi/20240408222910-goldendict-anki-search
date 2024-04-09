import argparse
import requests

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
            # Фильтруем только поле "WordDestination" для каждой заметки
            word_destinations = [note["fields"]["WordDestination"]["value"] for note in result["result"]]
            return word_destinations
            # return result
        else:
            print("Ошибка при получении всех полей заметок:", response.status_code)
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
    print("Результаты поиска:", result)
