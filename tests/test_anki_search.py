
import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import importlib.util

# Helper to import the target script which has a hyphen in the name
def import_anki_search():
    # Adjust path to point to the parent directory where anki-search.py resides
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'anki-search.py'))
    spec = importlib.util.spec_from_file_location("anki_search", script_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["anki_search"] = module
    spec.loader.exec_module(module)
    return module

anki_search = import_anki_search()

class TestAnkiSearch(unittest.TestCase):

    def setUp(self):
        # Reset defaults for tests
        anki_search.SEPARATOR_CHARS = ['.', ',', ':', ';', '?', '!', '—']
        anki_search.ANCHOR_LENGTH = 4

    def test_extract_anchors_simple(self):
        query = "This is a simple query without punctuation"
        start, end = anki_search.extract_anchors(query)
        self.assertEqual(start, "This is a simple")
        self.assertEqual(end, "simple query without punctuation")


    def test_extract_anchors_short(self):
        query = "Short query"
        start, end = anki_search.extract_anchors(query)
        self.assertEqual(start, "Short query")
        self.assertEqual(end, "Short query")

    def test_extract_anchors_punctuation_start(self):
        # "Hello, world" -> First word "Hello" matches separator char ","?
        # Our logic: has_separator("Hello,") is True.
        # It strips comma -> "Hello". Returns "Hello".
        query = "Hello, this is a test"
        start, end = anki_search.extract_anchors(query)
        self.assertEqual(start, "Hello")
        self.assertEqual(end, "this is a test")


    def test_extract_anchors_punctuation_middle(self):
        # "First second, third fourth"
        # Start: "First second". "second," triggers stop.
        query = "First second, third fourth fifth sixth"
        start, end = anki_search.extract_anchors(query)
        # "First" -> ok
        # "second," -> has comma. Strip -> "second". Append and break.
        self.assertEqual(start, "First second")
        
        # End: "sixth" "fifth" "fourth" "third"
        self.assertEqual(end, "third fourth fifth sixth")

    def test_extract_anchors_punctuation_end_logic(self):
        # "Start... end."
        query = "Start sentence here. End sentence here."
        start, end = anki_search.extract_anchors(query)
        # Start: "Start sentence here" ("here." has dot)
        self.assertEqual(start, "Start sentence here")
        
        # End: "End sentence here" (Scanning backwards: "here." (stripped->here) -> "sentence" -> "End" -> "here." (stop))
        # Wait, backward scan:
        # words = ["Start", "sentence", "here.", "End", "sentence", "here."]
        # reversed = ["here.", "sentence", "End", "here.", "sentence", "Start"]
        # 1. "here." -> has dot. Strip -> "here". Append. STOP.
        # So End anchor should be just "here".
        # Let's verify logic:
        # "if clean_w: end_anchor_words.append(clean_w); break"
        # Yes.
        self.assertEqual(end, "here")

    @patch('anki_search.invoke_ac')
    def test_search_range_in_deck(self, mock_invoke):
        # Setup Start/End Cards
        start_card = {'DeckName': '01-TestDeck', 'CardId': 100}
        end_card = {'DeckName': '01-TestDeck', 'CardId': 200}
        
        # Mock findCards response (returns list of ALL IDs in deck)
        # We need IDs 100, 150, 200 to be found. 50 should be ignored. 250 ignored.
        mock_invoke.side_effect = [
            [50, 100, 150, 200, 250], # findCards response
            # cardsInfo response
            [
                {'cardId': 100, 'fields': {'SentenceSource': {'value': 'Start'}}},
                {'cardId': 150, 'fields': {'SentenceSource': {'value': 'Middle'}}},
                {'cardId': 200, 'fields': {'SentenceSource': {'value': 'End'}}}
            ]
        ]
        
        # Query must match "StartMiddleEnd" when normalized
        original_query = "Start Middle End"
        
        results = anki_search.search_range_in_deck(start_card, end_card, original_query)
        
        # Verify findCards called with correct deck
        mock_invoke.assert_any_call('findCards', query='deck:"01-TestDeck"')
        
        # Verify cardsInfo called with filtered IDs
        mock_invoke.assert_any_call('cardsInfo', cards=[100, 150, 200])
        
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['CardId'], 100)
        self.assertEqual(results[1]['CardId'], 150)
        self.assertEqual(results[2]['CardId'], 200)

    @patch('anki_search.invoke_ac')
    def test_search_range_content_mismatch(self, mock_invoke):
        start_card = {'DeckName': '01-TestDeck', 'CardId': 100}
        end_card = {'DeckName': '01-TestDeck', 'CardId': 200}
        
        mock_invoke.side_effect = [
            [100, 200],
            [
                {'cardId': 100, 'fields': {'SentenceSource': {'value': 'Start'}}},
                {'cardId': 200, 'fields': {'SentenceSource': {'value': 'End'}}}
            ]
        ]
        
        # Mismatch query
        original_query = "Start SomethingElse End"
        
        results = anki_search.search_range_in_deck(start_card, end_card, original_query)
        self.assertEqual(results, [])

    @patch('anki_search.invoke_ac')
    def test_search_range_content_normalization(self, mock_invoke):
        start_card = {'DeckName': '01-TestDeck', 'CardId': 100}
        end_card = {'DeckName': '01-TestDeck', 'CardId': 200}
        
        mock_invoke.side_effect = [
            [100, 200],
            [
                {'cardId': 100, 'fields': {'SentenceSource': {'value': '  Start  '}}},
                {'cardId': 200, 'fields': {'SentenceSource': {'value': 'End.'}}}
            ]
        ]
        
        # Query with different spacing/case/punctuation
        # Note: logic only strips whitespace, not punctuation from content?
        # User requirement: "remove all spaces... to compare only the content part. And... lower case"
        # My implementation of `normalize_text` removes WHITESPACE and lowers. It does NOT remove punctuation.
        # But `_strip_html` might handle tags. 
        # If "End." in card and "End" in query -> Mismatch if dot exists.
        # Let's assume strict content match including punctuation is desired, but ignoring format (spaces).
        # Adjust test to match expected behavior.
        
        original_query = "start end."
        
        results = anki_search.search_range_in_deck(start_card, end_card, original_query)
        self.assertEqual(len(results), 2)


    def test_search_range_invalid_deck(self):
        # Deck doesn't start with 0
        start_card = {'DeckName': 'TestDeck', 'CardId': 100}
        end_card = {'DeckName': 'TestDeck', 'CardId': 200}
        results = anki_search.search_range_in_deck(start_card, end_card, "query")
        self.assertEqual(results, [])

    def test_search_range_different_decks(self):
        start_card = {'DeckName': '01-DeckA', 'CardId': 100}
        end_card = {'DeckName': '01-DeckB', 'CardId': 200}
        results = anki_search.search_range_in_deck(start_card, end_card, "query")
        self.assertEqual(results, [])

    @patch('anki_search.invoke_ac')
    def test_real_monitor_theory_example(self, mock_invoke):
        """
        Test based on real user data from request 20260117203810.
        Verifies that a paragraph broken into multiple phrase cards is correctly retrieved and verified.
        """
        full_text = (
            'This book is concerned with what has been called the "Monitor Theory" of adult second language acquisition. '
            'Monitor Theory hypothesizes that adults have two independent systems for developing ability in second languages, '
            'subconscious language acquisition and conscious language learning, '
            'and that these systems are interrelated in a definite way: '
            'subconscious acquisition appears to be far more important.'
        )

        start_card = {'DeckName': '01-RealDeck', 'CardId': 1000}
        end_card = {'DeckName': '01-RealDeck', 'CardId': 1004}

        # Mock findCards: Returns IDs for all cards in the sequence (plus some extras/surrounding)
        mock_invoke.side_effect = [
            [999, 1000, 1001, 1002, 1003, 1004, 1005], # findCards
            # cardsInfo
            [
                {'cardId': 1000, 'fields': {'SentenceSource': {'value': 'This book is concerned with what has been called the "Monitor Theory" of adult second language acquisition.'}}},
                {'cardId': 1001, 'fields': {'SentenceSource': {'value': 'Monitor Theory hypothesizes that adults have two independent systems for developing ability in second languages,'}}},
                {'cardId': 1002, 'fields': {'SentenceSource': {'value': 'subconscious language acquisition and conscious language learning,'}}},
                {'cardId': 1003, 'fields': {'SentenceSource': {'value': 'and that these systems are interrelated in a definite way:'}}},
                {'cardId': 1004, 'fields': {'SentenceSource': {'value': 'subconscious acquisition appears to be far more important.'}}}
            ]
        ]
        
        results = anki_search.search_range_in_deck(start_card, end_card, full_text)
        
        # Should return all 5 cards
        self.assertEqual(len(results), 5)
        self.assertEqual(results[0]['SentenceSource'], 'This book is concerned with what has been called the "Monitor Theory" of adult second language acquisition.')
        self.assertEqual(results[4]['SentenceSource'], 'subconscious acquisition appears to be far more important.')
        
        # Verify text normalization worked (query has newlines/spaces that might differ slightly, but verify logic normalizes them)



if __name__ == '__main__':
    unittest.main()
