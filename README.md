# Anki Search Utility

A command-line utility to interact with Anki via the AnkiConnect add-on.

[![Version](https://img.shields.io/badge/version-v1.44.2-blue)](https://github.com/voothi/20240408222910-goldendict-anki-search) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This script provides two main functionalities for interacting with your Anki collection from the command line:

-   **Advanced Card Search**: Perform complex searches for cards and print the results directly to your console in either plain text or HTML format.
-   **Direct Browser Integration**: Instantly open the Anki Card Browser with a specific search query, either provided as an argument or taken directly from your system clipboard.
-   **GoldenDict Integration**: Designed to work seamlessly with GoldenDict via an [accompanying AutoHotkey script](https://github.com/voothi/20240411110510-autohotkey), allowing you to look up selected words in Anki with a single hotkey.

## Table of Contents

- [Anki Search Utility](#anki-search-utility)
  - [Table of Contents](#table-of-contents)
  - [Usage](#usage)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Integration with GoldenDict (via AutoHotkey)](#integration-with-goldendict-via-autohotkey)
    - [Configuration](#configuration)
    - [How to Use](#how-to-use)
  - [How It Works](#how-it-works)
  - [Kardenwort Ecosystem](#kardenwort-ecosystem)
  - [License](#license)

---

## Usage

The script is controlled via command-line arguments.

| Argument               | Description                                                                                             | Required |
| ---------------------- | ------------------------------------------------------------------------------------------------------- | :------: |
| `--query`              | The word or phrase to search for in Anki notes.                                                         |    No    |
| `--search-type`        | Type of search: `word` (default) or `sentence`. Affects which fields are queried.                       |    No    |
| `--html`               | If present, outputs search results with HTML formatting preserved.                                      |    No    |
| `--browse-query`       | A query string to open directly in the Anki Card Browser (e.g., `"deck:MyDeck is:due"`).                |    No    |
| `--browse-clipboard`   | If present, uses the content of the system clipboard as the query to open in the Anki Card Browser.     |    No    |

[Back to Top](#table-of-contents)

## Prerequisites

1.  **Anki**: The script requires the Anki desktop application to be running.
2.  **AnkiConnect Add-on**: You must have the [AnkiConnect add-on](https://ankiweb.net/shared/info/2055492159) installed in Anki.
3.  **Python 3**: Python 3 must be installed on your system.

## Installation

1.  Clone this repository:
    ```bash
    git clone https://github.com/voothi/20240408222910-goldendict-anki-search.git
    ```
2.  Navigate to the repository folder:
    ```bash
    cd 20240408222910-goldendict-anki-search
    ```
3.  Install the required Python libraries:
    ```bash
    pip install requests pyperclip
    ```
4.  Make sure Anki **is running** in the background with the AnkiConnect add-on enabled.
5.  Run the script from your terminal to test it.

**Example Commands:**

```bash
# Search for the word "example" and print results as plain text
./anki-search.py --query "example"

# Search for a sentence and print results in HTML format
./anki-search.py --query "this is a test sentence" --search-type sentence --html

# Open the Anki browser to show all due cards in the "French" deck
./anki-search.py --browse-query "deck:French is:due"

# Open the Anki browser with a query taken from the clipboard (used for integration)
./anki-search.py --browse-clipboard
```

[Back to Top](#table-of-contents)

## Integration with GoldenDict (via AutoHotkey)

This script is most powerful when combined with the [accompanying AutoHotkey (AHK) script](https://github.com/voothi/20240411110510-autohotkey) to look up words from GoldenDict in Anki instantly.

### Configuration

1.  Download or clone the [AutoHotkey script repository](https://github.com/voothi/20240411110510-autohotkey).
2.  Open the `open-in-anki.ahk` file in a text editor.
3.  **You must update the paths** at the top of the script to match your system's configuration:
    ```ahk
    ; --- User Configuration ---
    ; You must update these paths to match your system's configuration.
    pythonPath := "C:\Path\To\Your\Python\python.exe"
    scriptPath := "C:\Path\To\Your\anki-search.py"
    ```
4.  Save the `open-in-anki.ahk` file and run it by double-clicking. It will run in the background.

### How to Use

Once the AHK script is configured and running, you have two ways to search from GoldenDict:

1.  **Hotkey Method**:
    -   In GoldenDict, select any word or phrase.
    -   Press `Ctrl+Alt+A`.
    -   The Anki Card Browser will open and execute a search for the selected text.

2.  **GoldenDict Program Method**:
    -   In GoldenDict, go to `Edit` -> `Dictionaries` -> `Programs` tab.
    -   Click `Add`.
    -   Set the **Type** to `Audio`.
    -   In the **Command Line** field, enter the full path to the AHK script followed by the `/trigger` argument. Use `%GDWORD%` to pass the search term.
        ```
        "C:\Path\To\Your\open-in-anki.ahk" /trigger
        ```
    -   Now, when you look up a word in GoldenDict, a new "play" icon will appear. Clicking it will trigger the search in Anki.

[Back to Top](#table-of-contents)

## How It Works

-   **AnkiConnect API**: The script communicates with a running Anki instance through the AnkiConnect add-on, which exposes an API at `http://localhost:8765`. All actions, like finding cards or opening the browser, are sent as JSON-RPC requests.
-   **Search Logic**: When using the `--query` argument, the script constructs a specific search query tailored to find terms in `WordSource`, `WordSourceInflectedForm`, or `SentenceSource` fields. This logic is hardcoded in the `search_word_in_decks` function and can be modified to fit different note types.
-   **Clipboard Bridge**: The `--browse-clipboard` argument acts as a bridge for other applications. The AutoHotkey script copies the selected text to the clipboard and then calls this Python script with that argument, which in turn tells Anki to search for the clipboard's content.

[Back to Top](#table-of-contents)

## Kardenwort Ecosystem

This project is part of the **[Kardenwort](https://github.com/kardenwort)** environment, designed to create a focused and efficient learning ecosystem.

[Return to Top](#table-of-contents)

## License

[MIT](./LICENSE)

[Back to Top](#table-of-contents)
