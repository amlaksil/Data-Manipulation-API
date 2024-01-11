#!/usr/bin/python3

"""
Contains tests for json-to-csv endpoint.
"""

import unittest
import requests
import filecmp
import pep8
from os import getenv

from parameterized import parameterized
import pandas as pd


def compare_csv_files(file_path_1, file_path_2):
    """
    Compares two CSV files and checks if they have identical
    columns and values.

    Args:
            file_path_1 (str): The path to the first CSV file.
            file_path_2 (str): The path to the second CSV file.

    Returns:
            bool: True if the CSV files have indentical columns and
    values, False otherwise.
    """
    # Read the CSV files into pandas DataFrames
    df1 = pd.read_csv(file_path_1)
    df2 = pd.read_csv(file_path_2)

    # Retrieve the column names and sort them
    column_names_1 = sorted(df1.columns.tolist())
    column_names_2 = sorted(df2.columns.tolist())

    # Check if the column names are identical
    if column_names_1 != column_names_2:
        return False

    # Compare values in each column
    for column in column_names_1:
        if df1[column].tolist() != df2[column].tolist():
            return False

    return True


class TestJSONToCSVDocs(unittest.TestCase):
    """
    Tests to check the documentation and style of json-to-csv endpoint.
    """

    def test_pep8_conformance_test_csv_to_json(self):
        """Test that test_json_to_csv conforms to PEP8."""
        pep8s = pep8.StyleGuide(quiet=True)
        result = pep8s.check_files(['tests/test_json_to_csv.py'])
        self.assertEqual(result.total_errors, 0, "Found code style errors" +
                         " (and warnings).")


class TestJSONToCSV(unittest.TestCase):
    def setUp(self):
        """Set up for json-to-csv tests."""
        self.base_url = 'http://localhost:5000/api/v1'
        self.username = str(getenv('DM_API_USERNAME'))
        self.password = str(getenv('DM_API_PASSWORD'))
        self.email = str(getenv('DM_API_EMAIL'))

    def test_with_missing_access_token(self):
        """
        Test that an appropriate error is raised when the access token is
        missing from the request header.
        """
        endpoint = self.base_url + '/json-to-csv'
        response = requests.post(endpoint)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], 'Token is missing!')

    def test_with_invalid_access_token(self):
        """
        Test that an appropriate error is raised when an invalid access
        token is used.
        """
        endpoint = self.base_url + '/json-to-csv'
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
        endpoint = self.base_url + '/json-to-csv'
        headers = {
            'Content-Type': 'application/json',
            'access-token': token
        }
        response = requests.post(endpoint, headers=headers)

    def test_with_invalid_content_type(self):
        """
        Test that an appropriate error is raised when an invalid
        content-type is used.
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
        headers = {
            'access-token': token,
            'Content-Type': 'txt/csv'
        }
        endpoint = self.base_url + '/json-to-csv'
        response = requests.post(endpoint, headers=headers)

        self.assertEqual(response.status_code, 415)
        self.assertEqual(
            response.json()['error'], "Invalid Content-Type. Expected " +
            "'application/json' or 'multipart/form-data'")

    @parameterized.expand([
        ('datasets/valid-csv-1.csv',),
        ('datasets/file.txt',)
    ])
    def test_with_invalid_file_extension(self, path):
        """
        Test that an appropriate error is raised when a file with an
        invalid extension is used.
        """
        with open(path, 'rb') as file:
            files = [
                ('file', file)
            ]

            response = requests.get(
                self.base_url + '/login', auth=(self.username, self.password))
            self.assertEqual(response.status_code, 200)

            token = response.json()['token']
            endpoint = self.base_url + '/json-to-csv'

            with requests.post(endpoint,
                               headers={'access-token': token},
                               files=files) as response:
                if path == 'datasets/file.txt':
                    extension = 'txt'
                else:
                    extension = 'csv'
            self.assertEqual(response.status_code, 400)
            self.assertEqual(
                response.json()['error'], 'Invalid file type. The uploaded' +
                f' file has a \'{extension}\' extension. ' +
                'Only JSON files are supported.')

    def test_with_invalid_payload_expect_list(self):
        """
        Test that an appropriate error is raised when an invalid payload
        is provided, expecting a list.
        """
        response = requests.get(self.base_url + '/login',
                                auth=(self.username, self.password))
        self.assertEqual(response.status_code, 200)

        token = response.json()['token']
        endpoint = self.base_url + '/json-to-csv'
        headers = {
            'Content-Type': 'application/json',
            'access-token': token
        }
        payload = {"data": {}}

        response = requests.post(endpoint, json=payload, headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'],
                         'Invalid JSON data. Expected a list.')

    def test_with_empty_payload_expect_error(self):
        """
        Test that an appropriate error is raised when an empty
        payload is provided.
        """
        response = requests.get(self.base_url + '/login',
                                auth=(self.username, self.password))
        self.assertEqual(response.status_code, 200)

        payload = {"data": []}
        token = response.json()['token']
        endpoint = self.base_url + '/json-to-csv'
        headers = {
            'Content-Type': 'application/json',
            'access-token': token
        }

        payload = {"data": []}

        response = requests.post(endpoint, json=payload, headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'],
                         'Empty JSON array. No data to convert.')

    def test_with_invalid_payload_expect_list_of_dicts(self):
        """
        Test that an appropriate error is raised when an invalid payload
        is provided, expecting a list of dictionaries.
        """
        response = requests.get(self.base_url + '/login',
                                auth=(self.username, self.password))
        self.assertEqual(response.status_code, 200)

        token = response.json()['token']
        endpoint = self.base_url + '/json-to-csv'
        headers = {
            'Content-Type': 'application/json',
            'access-token': token
        }
        payload = {"data": [{"id": 1, "name": "John", "age": 25}, {
            "id": 2, "name": "Jane", "age": 30}, "name", "student"]}
        response = requests.post(endpoint, json=payload, headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()['error'], 'Invalid JSON data. Expected a ' +
            'list of dictionaries.')

    @parameterized.expand([
        ('datasets/d1.json', 'datasets/merge-csv-1.csv'),
        ('datasets/d2.json', 'datasets/merge-csv-2.csv'),
        ('datasets/d3.json', 'datasets/merge-csv-3.csv'),
        ('datasets/d4.json', 'datasets/merge-csv-4.csv')
    ])
    def test_with_valid_file(self, path, output):
        """
        Test that the conversion from the input json to the output csv
        format is successful.
        """
        response = requests.get(self.base_url + '/login',
                                auth=(self.username, self.password))
        self.assertEqual(response.status_code, 200)

        token = response.json()['token']
        endpoint = self.base_url + '/json-to-csv'

        with open(path, 'rb') as file:
            response = requests.post(
                endpoint, headers={'access-token': token},
                files={'file': file})
            self.assertEqual(response.status_code, 200)
            with open('datasets/data.csv', 'wb') as f:
                f.write(response.content)
            self.assertTrue(compare_csv_files('datasets/data.csv', output))


if __name__ == '__main__':
    unittest.main()
