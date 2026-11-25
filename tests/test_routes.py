import unittest

from main import app


class RouteTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_index_redirects_to_kinopoisk(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "https://www.kinopoisk.ru/")

    def test_mirror_redirects_to_kinokino(self):
        response = self.client.get(
            "/mirror",
            query_string={"url": "https://www.kinopoisk.ru/film/464963/"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.headers["Location"],
            "https://www.kinokino.win/film/464963/",
        )

    def test_mirror_rejects_an_unsupported_page(self):
        response = self.client.get(
            "/mirror",
            query_string={"url": "https://www.kinopoisk.ru/"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Эта ссылка не подходит", response.get_data(as_text=True))

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_data(as_text=True), "ok")


if __name__ == "__main__":
    unittest.main()
