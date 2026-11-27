import unittest

from main import app


class RouteTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_index_serves_custom_interface(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("KinoKino", response.get_data(as_text=True))

    def test_api_search_returns_results(self):
        response = self.client.get(
            "/api/search",
            query_string={"q": "Inception"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("results", data)

    def test_api_search_empty_query(self):
        response = self.client.get("/api/search", query_string={"q": ""})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["results"], [])

    def test_api_film_endpoint(self):
        response = self.client.get("/api/film/464963")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["id"], 464963)
        self.assertIn("kinokino.win", data["mirror_url"])

    def test_watch_page_renders_player(self):
        response = self.client.get("/watch/326")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("hls.min.js", html)
        self.assertIn("filmId = 326", html)
        self.assertIn("/api/film/", html)

    def test_streams_endpoint_shape(self):
        response = self.client.get("/api/film/326/streams")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("results", data)
        self.assertIsInstance(data["results"], list)

    def test_manifest_proxy_requires_url(self):
        response = self.client.get("/stream/manifest")
        self.assertEqual(response.status_code, 400)

    def test_segment_proxy_requires_url(self):
        response = self.client.get("/stream/segment")
        self.assertEqual(response.status_code, 400)

    def test_manifest_proxy_rejects_non_http(self):
        response = self.client.get("/stream/manifest", query_string={"url": "file:///etc/passwd"})
        self.assertEqual(response.status_code, 400)

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_data(as_text=True), "ok")


if __name__ == "__main__":
    unittest.main()
