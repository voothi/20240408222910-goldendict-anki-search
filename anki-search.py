import argparse
import requests

def search_word_in_deck(deck_name, search_word):
    # Адрес сервера Anki Connect
    anki_connect_url = "http://localhost:8765"
    
    # Формируем запрос для поиска слова в колоде
    payload = {
        "action": "findNotes",
        "version": 6,
        "params": {
            "query": f"deck:'{deck_name}' {search_word}"
        }
    }
    
    # Отправляем запрос
    response = requests.post(anki_connect_url, json=payload)
    
    # Обрабатываем результат
    if response.status_code == 200:
        result = response.json()
        return result["result"]
    else:
        print("Ошибка при отправке запроса:", response.status_code)
        return None

if __name__ == "__main__":
    # Парсинг аргументов командной строки
    parser = argparse.ArgumentParser(description="Search for a word in a specific Anki deck")
    parser.add_argument("deck_name", help="Name of the Anki deck to search in")
    parser.add_argument("search_word", help="Word to search for in the Anki deck")
    args = parser.parse_args()

    # Выполнение поиска
    result = search_word_in_deck(args.deck_name, args.search_word)
    print("Результаты поиска:", result)
