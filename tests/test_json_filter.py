#!/usr/bin/python3

"""
Contains tests for json-filter endpoint.
"""

import unittest
import requests
import filecmp
import pep8
from os import getenv

from parameterized import parameterized


class TestJSONFilterDocs(unittest.TestCase):
    """
    Tests to check the documentation and style of json-filter endpoint.
    """
    def test_pep8_conformance_test_csv_to_json(self):
        """Test that test_json_filter conforms to PEP8."""
        pep8s = pep8.StyleGuide(quiet=True)
        result = pep8s.check_files(['tests/test_json_filter.py'])
        self.assertEqual(result.total_errors, 0, "Found code style errors" +
                         " (and warnings).")


class TestJSONFilter(unittest.TestCase):
    def setUp(self):
        """Set up for json-filter tests"""
        self.base_url = 'http://localhost:5000/api/v1'

    def test_with_missing_file(self):
        """
        Test that an appropriate error is raised when a required
        file is missing.
        """
        endpoint = self.base_url + '/json-filter'

        headers = {"Content-Type": "multipart/form-data"}

        response = requests.post(endpoint, headers=headers)

        # Assert the response status code and error message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()['error'], 'No file found in the request. Please ' +
            'include a file in the \'file\' field.')

    def test_with_invalid_content_type(self):
        """
        Test that an appropriate error is raised when invalild
        Content-Type is used.
        """

        endpoint = self.base_url + '/json-filter'
        response = requests.post(endpoint)

        # Assert the response status code and error message
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
        Test that an appropriate error is raised when a file with
        an invalid extension is used.
        """
        endpoint = self.base_url + '/json-filter'

        with open(path, 'rb') as file:
            files = [('file', file)]
            with requests.post(endpoint, files=files) as response:
                if path == 'datasets/file.txt':
                    extension = 'txt'
                else:
                    extension = 'csv'
            self.assertEqual(response.status_code, 400)
            self.assertEqual(
                response.json()['error'], 'Invalid file type. The uploaded ' +
                f'file has a \'{extension}\' extension. ' +
                'Only JSON files are supported.')

    @parameterized.expand([
        ('datasets/d1.json',)
    ])
    def test_without_setting_criteria(self, path):
        """
        Test that an appropriate error response is generated when criteria are
        not set before processing the file.
        """
        endpoint = self.base_url + '/json-filter'

        with open(path, 'rb') as file:
            response = requests.post(endpoint, files={'file': file})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()['error'], 'You must set a filter criteria before' +
            ' starting the filtering process.')

    @parameterized.expand([
        ('datasets/d1.json',)
    ])
    def test_by_setting_criteria_as_non_dict_type(self, path):
        """
        Test that an appropriate error response is generated when the criteria
        is set as a non-dictionary type.
        """
        endpoint = self.base_url + '/json-filter'
        headers = {'criteria': 'Silamlak'}

        with open(path, 'rb') as file:
            response = requests.post(
                endpoint, headers=headers, files={'file': file})

            self.assertEqual(response.status_code, 400)
            self.assertEqual(
                response.json()['error'], 'Invalid JSON format in criteria' +
                ' header. It should be dictionary object.')

    @parameterized.expand([
        ('datasets/d1.json',)
    ])
    def test_with_empty_criteria(self, path):
        """
        Test that an appropriate error response is generated when the criteria
        is an empty dictionary.
        """
        endpoint = self.base_url + '/json-filter'
        headers = {'criteria': '{}'}

        with open(path, 'rb') as file:
            response = requests.post(
                endpoint, headers=headers, files={'file': file})

            self.assertEqual(response.status_code, 400)
            self.assertEqual(
                response.json()['error'], "Empty criteria or dictionary: " +
                "'criteria: {}'")

    @parameterized.expand([
        ('datasets/d1.json',)
    ])
    def test_with_invalid_criteria_format(self, path):
        """
        Test that an appropriate error response is generated when the criteria
        has an invalid format.
        """
        endpoint = self.base_url + '/json-filter'
        headers = {'criteria': '{"fname": "Silamlak"}'}

        with open(path, 'rb') as file:
            response = requests.post(
                endpoint, headers=headers, files={'file': file})

            self.assertEqual(response.status_code, 400)
            self.assertEqual(
                response.json()['error'], "The 'criteria' value should be " +
                "in the following format: '<criteria>: {<key> : {<operator>:" +
                " <value to be compared>}}'." +
                ' Example: criteria: {"Age": {"gt": 18}}')

    @parameterized.expand([
        ('datasets/d1.json',)
    ])
    def test_with_key_without_operator(self, path):
        """
        Test that an appropriate error response is generated when a key
        is provided without an operator in the criteria.
        """
        endpoint = self.base_url + '/json-filter'
        headers = {'criteria': '{"Age": {}}'}

        with open(path, 'rb') as file:
            response = requests.post(
                endpoint, headers=headers, files={'file': file})

            self.assertEqual(response.status_code, 400)
            self.assertEqual(
                response.json()['error'], "key without operator 'criteria:" +
                " {'key': {}}'")

    @parameterized.expand([
        ('datasets/d1.json',)
    ])
    def test_with_invalid_operator(self, path):
        """
        Test that an appropriate error response is generated when an invalid
        operator is used in the criteria.
        """
        endpoint = self.base_url + '/json-filter'
        headers = {'criteria': '{"Age": {"less-than": 30}}'}

        with open(path, 'rb') as file:
            response = requests.post(
                endpoint, headers=headers, files={'file': file})

            self.assertEqual(response.status_code, 400)
            self.assertEqual(
                response.json()['error'], 'You have used invalid operator. ' +
                "Please use one of the following instead: " +
                "['eq, 'ne', 'gt', 'lt', 'gte', 'lte']")

    @parameterized.expand([
        ('datasets/d2.json', 'datasets/fdata-1.json'),
        ('datasets/d2.json', 'datasets/fdata-2.json'),
        ('datasets/d2.json', 'datasets/fdata-3.json'),
        ('datasets/d2.json', 'datasets/fdata-4.json'),
        ('datasets/d2.json', 'datasets/fdata-5.json'),
        ('datasets/d2.json', 'datasets/fdata-6.json')
    ])
    def test_with_valid_file(self, path, output):
        """Test that the JSON filtering is successful."""

        endpoint = self.base_url + '/json-filter'

        if output == 'datasets/fdata-1.json':
            operator = 'eq'
        elif output == 'datasets/fdata-2.json':
            operator = 'ne'
        elif output == 'datasets/fdata-3.json':
            operator = 'gt'
        elif output == 'datasets/fdata-4.json':
            operator = 'lt'
        elif output == 'datasets/fdata-5.json':
            operator = 'gte'
        elif output == 'datasets/fdata-6.json':
            operator = 'lte'

        headers = {'criteria': '{"Age": {' + f'"{operator}" ' + ': 30}}'}
        with open(path, 'rb') as file:
            response = requests.post(
                endpoint, headers=headers, files={'file': file})

            self.assertEqual(response.status_code, 200)
            with open('datasets/filtered-data.json', 'wb') as f:
                f.write(response.content)
            self.assertTrue(filecmp.cmp('datasets/filtered-data.json', output))


if __name__ == '__main__':
    unittest.main()
