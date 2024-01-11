#!/usr/bin/python3

"""
Contains the test class for csv-to-json endpoint.
"""

import unittest
import requests
import filecmp
import pep8
from os import getenv

from api.v1.views import app, db, data
from parameterized import parameterized


class TestCSVToJSONDocs(unittest.TestCase):
    """
    Tests to check the documentation and style of csv-to-json endpoint.
    """
    def test_pep8_conformance_test_csv_to_json(self):
        """Test that test_csv_to_json conforms to PEP8."""
        pep8s = pep8.StyleGuide(quiet=True)
        result = pep8s.check_files(['tests/test_csv_to_json.py'])
        self.assertEqual(result.total_errors, 0, "Found code style errors" +
                         " (and warnings).")


class TestCSVToJSON(unittest.TestCase):
    def setUp(self):
        """Set up for csv-to-json tests"""
        self.base_url = 'http://localhost:5000/api/v1'
        self.username = str(getenv('DM_API_USERNAME'))
        self.password = str(getenv('DM_API_PASSWORD'))
        self.email = str(getenv('DM_API_EMAIL'))

    def test_with_missing_access_token(self):
        """
        Test that an appropriate error is raised when the access token is
        missing from the request header.
        """
        endpoint = self.base_url + '/csv-to-json'
        response = requests.post(endpoint)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], 'Token is missing!')

    def test_with_invalid_access_token(self):
        """
        Test that an appropriate error is raised when an invalid access token
        is used.
        """

        endpoint = self.base_url + '/csv-to-json'
        response = requests.post(
            endpoint, headers={'access-token': 'silamlakdesye2014'})

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error'], 'Token is invalid!')

    def test_with_missing_file(self):
        """
        Test that an appropriate error is raised when a required file is
        missing.
        """
        payload = {
            'name': self.username,
            'password': self.password,
            'email': self.email
        }
        response = requests.post(self.base_url + '/user', json=payload)

        if response.status_code != 409:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['message'], 'New user created!')

        response = requests.get(self.base_url + '/login',
                                auth=(self.username, self.password))
        self.assertEqual(response.status_code, 200)

        token = response.json()['token']
        endpoint = self.base_url + '/csv-to-json'
        response = requests.post(endpoint, headers={'access-token': token})

        # Assert the response status code and error message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'],
                         'No file found in the request. Please include ' +
                         'a file in the \'file\' field.')

    @parameterized.expand([
        ('datasets/fdata-1.json',),
        ('datasets/file.txt',)
    ])
    def test_with_invalid_file_extension(self, path):
        """
        Test that an appropriate error is raised when a file with an invalid
        extension is used.
        """
        with open(path, 'rb') as file:
            files = [('file', file)]

            response = requests.get(
                self.base_url + '/login', auth=(self.username, self.password))
            self.assertEqual(response.status_code, 200)
            token = response.json()['token']

            endpoint = self.base_url + '/csv-to-json'
            with requests.post(
                    endpoint,
                    headers={'access-token': token}, files=files) as response:
                if path == 'datasets/file.txt':
                    extension = 'txt'
                else:
                    extension = 'json'
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json()['error'],
                                 'Invalid file type. The uploaded file has ' +
                                 f'a \'{extension}\' extension. Only CSV ' +
                                 'files are supported.')

    @parameterized.expand([
        ('datasets/merge-csv-1.csv', 'datasets/d1.json'),
        ('datasets/merge-csv-2.csv', 'datasets/d2.json'),
        ('datasets/merge-csv-3.csv', 'datasets/d3.json'),
        ('datasets/merge-csv-4.csv', 'datasets/d4.json')
    ])
    def test_with_valid_file(self, path, output):
        """Test that the conversion from the input csv to the output json
        format is successful.
        """
        response = requests.get(self.base_url + '/login',
                                auth=(self.username, self.password))
        self.assertEqual(response.status_code, 200)

        token = response.json()['token']
        endpoint = self.base_url + '/csv-to-json'

        with open(path, 'rb') as file:
            response = requests.post(
                endpoint, headers={'access-token': token},
                files={'file': file})
            self.assertEqual(response.status_code, 200)
            with open('datasets/data.json', 'wb') as f:
                f.write(response.content)
            self.assertTrue(filecmp.cmp('datasets/data.json', output))


if __name__ == '__main__':
    unittest.main()
