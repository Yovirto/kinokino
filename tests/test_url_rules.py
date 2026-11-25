import unittest

from url_rules import build_mirror_url


class BuildMirrorUrlTests(unittest.TestCase):
    def test_movie_url(self):
        self.assertEqual(
            build_mirror_url("https://www.kinopoisk.ru/film/464963/"),
            "https://www.kinokino.win/film/464963/",
        )

    def test_series_url(self):
        self.assertEqual(
            build_mirror_url("https://www.kinopoisk.ru/series/123456/"),
            "https://www.kinokino.win/series/123456/",
        )

    def test_first_segment_can_be_any_value(self):
        self.assertEqual(
            build_mirror_url("https://www.kinopoisk.ru/anything/42/"),
            "https://www.kinokino.win/anything/42/",
        )

    def test_www_is_optional_in_source_url(self):
        self.assertEqual(
            build_mirror_url("https://kinopoisk.ru/film/42/"),
            "https://www.kinokino.win/film/42/",
        )

    def test_query_and_fragment_are_preserved(self):
        self.assertEqual(
            build_mirror_url(
                "https://www.kinopoisk.ru/series/42/?tab=details#actors"
            ),
            "https://www.kinokino.win/series/42/?tab=details#actors",
        )

    def test_missing_trailing_slash_is_accepted(self):
        self.assertEqual(
            build_mirror_url("https://www.kinopoisk.ru/film/42"),
            "https://www.kinokino.win/film/42",
        )

    def test_home_page_is_rejected(self):
        self.assertIsNone(build_mirror_url("https://www.kinopoisk.ru/"))

    def test_non_numeric_id_is_rejected(self):
        self.assertIsNone(
            build_mirror_url("https://www.kinopoisk.ru/film/not-a-number/")
        )

    def test_extra_path_segment_is_rejected(self):
        self.assertIsNone(
            build_mirror_url("https://www.kinopoisk.ru/film/42/actors/")
        )

    def test_another_host_is_rejected(self):
        self.assertIsNone(
            build_mirror_url("https://example.com/film/42/")
        )

    def test_lookalike_host_is_rejected(self):
        self.assertIsNone(
            build_mirror_url("https://www.kinopoisk.ru.example.com/film/42/")
        )

    def test_non_http_scheme_is_rejected(self):
        self.assertIsNone(build_mirror_url("javascript:alert(1)"))

    def test_empty_url_is_rejected(self):
        self.assertIsNone(build_mirror_url(""))
        self.assertIsNone(build_mirror_url(None))


if __name__ == "__main__":
    unittest.main()
