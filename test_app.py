import unittest
from unittest.mock import patch, Mock
from app import app, fetch_movie_details, fetch_flag_async

class MovieWithFlagAppTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Set up a Flask test client for the entire test class
        cls.client = app.test_client()
        app.config['TESTING'] = True

    def notest_integration(self):
        response = self.client.get("/api/movies?filter=superman")
        self.assertEqual(response.status_code, 200)

        # The response should be JSON and contain data
        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 10)
        for movie in data:
            self.assertIsNotNone(movie["title"])
            self.assertIsNotNone(movie["year"])
            self.assertIsNotNone(movie["countries"])

    @patch("app.search_movies")
    @patch("app.fetch_movie_details")
    def test_movie_flag_get(self, mock_fetch_movie_details, mock_search_movies):
        mock_fetch_movie_details.return_value = {
            "Title": "Superman II",
            "Year": "1980",
            "Country": "United States, United Kingdom, Canada, France",
        }
        mock_search_movies.return_value = {
            "Search": [
                {
                    "Title": "Superman II",
                    "Year": "1980",
                    "imdbID": "tt0081573"
                }
            ]
        }

        response = self.client.get("/api/movies?filter=superman")
        self.assertEqual(response.status_code, 200)

        # The response should be JSON and contain data
        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        for movie in data:
            self.assertEqual(movie["title"], "Superman II")
            self.assertEqual(movie["year"], "1980")
            self.assertEqual(len(movie["countries"]), 4)
            self.assertEqual(movie["countries"][0]["name"], "United States")
            self.assertEqual(movie["countries"][1]["name"], "United Kingdom")
            self.assertEqual(movie["countries"][2]["name"], "Canada")
            self.assertEqual(movie["countries"][3]["name"], "France")
            self.assertEqual(movie["countries"][0]["flag"], "https://flagcdn.com/us.svg")
            self.assertEqual(movie["countries"][1]["flag"], "https://flagcdn.com/gb.svg")
            self.assertEqual(movie["countries"][2]["flag"], "https://flagcdn.com/ca.svg")
            self.assertEqual(movie["countries"][3]["flag"], "https://flagcdn.com/fr.svg")

    @patch("app.fetch_flag_async")
    @patch("app.fetch_movie_details")
    def test_movie_searchapi(self, mock_fetch_movie_details, mock_fetch_flag_async):
        mock_fetch_movie_details.return_value = {
            "Title": "Superman II",
            "Year": "1980",
            "Country": "United States, United Kingdom, Canada, France",
        }
        mock_fetch_flag_async.return_value = "https://flagcdn.com/us.svg"

        response = self.client.get("/api/movies?filter=superman")
        self.assertEqual(response.status_code, 200)

        # The response should be JSON and contain data
        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 10)
        for movie in data:
            self.assertEqual(movie["title"], "Superman II")
            self.assertEqual(movie["year"], "1980")
            self.assertEqual(len(movie["countries"]), 4)
            self.assertEqual(movie["countries"][0]["name"], "United States")
            self.assertEqual(movie["countries"][1]["name"], "United Kingdom")
            self.assertEqual(movie["countries"][2]["name"], "Canada")
            self.assertEqual(movie["countries"][3]["name"], "France")
            self.assertEqual(movie["countries"][0]["flag"], "https://flagcdn.com/us.svg")
            self.assertEqual(movie["countries"][1]["flag"], "https://flagcdn.com/us.svg")
            self.assertEqual(movie["countries"][2]["flag"], "https://flagcdn.com/us.svg")
            self.assertEqual(movie["countries"][3]["flag"], "https://flagcdn.com/us.svg")
