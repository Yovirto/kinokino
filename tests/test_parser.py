import unittest
from unittest.mock import patch

from kinopoisk_parser import search, _clean_item


class SuggestItemTests(unittest.TestCase):
    def test_clean_item(self):
        raw = {
            "id": 464963,
            "title": {"russian": "Дюна", "original": "Dune"},
            "rating": {"kinopoisk": {"value": 8.4}},
            "productionYear": 2021,
            "gallery": {
                "posters": {
                    "kpVertical": {
                        "avatarsUrl": "//cdn.example.com/poster.jpg"
                    }
                }
            },
        }
        item = _clean_item(raw)
        self.assertEqual(item["id"], 464963)
        self.assertEqual(item["title"], "Дюна")
        self.assertEqual(item["original_title"], "Dune")
        self.assertEqual(item["rating"], 8.4)
        self.assertEqual(item["year"], 2021)
        self.assertEqual(item["poster"], "https://cdn.example.com/poster.jpg")
        self.assertEqual(item["url"], "https://www.kinopoisk.ru/film/464963/")

    def test_clean_item_missing_fields(self):
        item = _clean_item({"id": 1})
        self.assertEqual(item["title"], "")
        self.assertIsNone(item["rating"])
        self.assertIsNone(item["year"])
        self.assertIsNone(item["poster"])

    def test_clean_item_none_id(self):
        self.assertIsNone(_clean_item({}))
        self.assertIsNone(_clean_item({"title": {}}))


class SearchTests(unittest.TestCase):
    @patch("kinopoisk_parser._SESSION.get")
    def test_search_returns_normalized_results(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status.return_value = None
        mock_get.return_value.json.return_value = {
            "suggest": {
                "top": {
                    "topResult": {
                        "global": {
                            "id": 447301,
                            "title": {
                                "russian": "Начало",
                                "original": "Inception",
                            },
                            "rating": {"kinopoisk": {"value": 8.672}},
                            "productionYear": 2010,
                            "gallery": {
                                "posters": {
                                    "kpVertical": {
                                        "avatarsUrl": "//cdn.example.com/a.jpg"
                                    }
                                }
                            },
                        }
                    },
                    "movies": [],
                    "series": [],
                    "people": [],
                }
            }
        }

        results = search("Inception")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], 447301)
        self.assertEqual(results[0]["title"], "Начало")
        self.assertEqual(results[0]["original_title"], "Inception")
        self.assertEqual(results[0]["rating"], 8.672)
        self.assertEqual(results[0]["year"], 2010)
        self.assertEqual(results[0]["poster"], "https://cdn.example.com/a.jpg")
        self.assertEqual(results[0]["url"], "https://www.kinopoisk.ru/film/447301/")

    @patch("kinopoisk_parser._SESSION.get")
    def test_search_empty_query(self, mock_get):
        self.assertEqual(search(""), [])
        self.assertEqual(search(None), [])
        mock_get.assert_not_called()

    @patch("kinopoisk_parser._SESSION.get")
    def test_search_http_error_returns_empty(self, mock_get):
        mock_get.side_effect = OSError("network down")
        self.assertEqual(search("anything"), [])
