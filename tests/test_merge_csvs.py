#!/usr/bin/python3

import unittest
import requests
import filecmp
import pep8
from os import getenv

from api.v1.views import app, db
from parameterized import parameterized


class TestMergeCSVsDocs(unittest.TestCase):
    """
    Tests to check the documentation and style of json-to-csv endpoint.
    """

    def test_pep8_conformance_test_csv_to_json(self):
        """Test that test_merge_csvs conforms to PEP8."""
        pep8s = pep8.StyleGuide(quiet=True)
        result = pep8s.check_files(['tests/test_merge_csvs.py'])
        self.assertEqual(result.total_errors, 0, "Found code style errors" +
                         " (and warnings).")


class TestMergeCSVs(unittest.TestCase):
    def setUp(self):
        """Set up for merge-csvs tests"""
        self.base_url = 'http://localhost:5000/api/v1'
        self.username = str(getenv('DM_API_USERNAME'))
        self.password = str(getenv('DM_API_PASSWORD'))
        self.email = str(getenv('DM_API_EMAIL'))

    def test_with_missing_access_token(self):
        """
        Test that an appropriate error is raised when the access token is
        missing from the request header.
        """
        endpoint = self.base_url + '/merge-csvs'
        response = requests.post(endpoint)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], 'Token is missing!')

    def test_with_invalid_access_token(self):
        """
        Test that an appropriate error is raised when an invalid
        access token is used.
        """
        endpoint = self.base_url + '/merge-csvs'
        response = requests.post(
            endpoint, headers={'access-token': 'silamlakdesye2014'})

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error'], 'Token is invalid!')

    def test_with_missing_file(self):
        """
        Test that an appropriate error is raised when a required
        file is missing.
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
        endpoint = self.base_url + '/merge-csvs'
        response = requests.post(endpoint, headers={'access-token': token})

        # Assert the response status code and error message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()['error'], 'No file found in the request. Please ' +
            'include files in the \'files\' field.')

    @parameterized.expand([
        ('datasets/valid-csv-1',)
    ])
    def test_with_one_file(self, path):
        """
        Test that an appropriate error response is generated when only a
        single file is passed.
        """

        response = requests.get(self.base_url + '/login',
                                auth=(self.username, self.password))
        self.assertEqual(response.status_code, 200)

        token = response.json()['token']
        endpoint = self.base_url + '/merge-csvs'
        response = requests.post(
            endpoint, headers={'access-token': token}, files={'files': path})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()['error'], 'You should include at least two ' +
            'files to continue merging.')

    @parameterized.expand([
        ('datasets/valid-csv-1.csv', 'datasets/fdata-1.json'),
        ('datasets/file.txt', 'datasets/fdata-1.json')
    ])
    def test_with_invalid_file_extension(self, path1, path2):
        """
        Test that an appropriate error is raised when a file with an
        invalid extension is used.
        """
        with open(path1, 'rb') as file1, open(path2, 'rb') as file2:
            files = [
                ('files', file1),
                ('files', file2)
            ]

            response = requests.get(
                self.base_url + '/login', auth=(self.username, self.password))
            self.assertEqual(response.status_code, 200)

            token = response.json()['token']
            endpoint = self.base_url + '/merge-csvs'

            with requests.post(endpoint,
                               headers={'access-token': token},
                               files=files) as response:
                if path1 == 'datasets/file.txt':
                    extension = 'txt'
                    file = 'file.txt'
                elif path2 == 'datasets/fdata-1.json':
                    extension = 'json'
                    file = 'fdata-1.json'
                self.assertEqual(response.status_code, 400)
                self.assertEqual(
                    response.json()['error'], 'Invalid file type. The ' +
                    f'uploaded {file} has a \'{extension}\' extension.' +
                    ' Only CSV files are supported.')

    @parameterized.expand([
        ('datasets/merge-csv-1.csv', 'datasets/merge-csv-2.csv',
         'inner', 'datasets/output-m.csv'),
        ('datasets/merge-csv-3.csv', 'datasets/merge-csv-4.csv',
         'inner', 'datasets/output-inner.csv'),
        ('datasets/merge-csv-3.csv', 'datasets/merge-csv-4.csv',
         'outer', 'datasets/output-outer.csv'),
        ('datasets/merge-csv-3.csv', 'datasets/merge-csv-4.csv',
         'left', 'datasets/output-left.csv'),
        ('datasets/merge-csv-3.csv', 'datasets/merge-csv-4.csv',
         'right', 'datasets/output-right.csv')
    ])
    def test_with_valid_csv_files_expect_successful_merge(
            self, path1, path2, technique, output):
        """
        Test that the merging of valid CSV files using the specified
        technique is successful.
        """
        with open(path1, 'rb') as f1, open(path2, 'rb') as f2:
            files = [
                ('files', f1),
                ('files', f2)
            ]

            response = requests.get(
                self.base_url + '/login', auth=(self.username, self.password))
            self.assertEqual(response.status_code, 200)

            token = response.json()['token']
            endpoint = self.base_url + '/merge-csvs' + \
                f'?technique={technique}'

            with requests.post(endpoint,
                               headers={'access-token': token},
                               files=files) as response:
                self.assertEqual(response.status_code, 200)
                with open('datasets/output.csv', 'wb') as f:
                    f.write(response.content)

                self.assertTrue(filecmp.cmp('datasets/output.csv', output))


if __name__ == '__main__':
    unittest.main()
