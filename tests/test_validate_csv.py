#!/usr/bin/python3

import unittest
import pep8
import requests

from parameterized import parameterized


class TestValidateCSVDocs(unittest.TestCase):
    """
    Tests to check the documentation and style of validate-csv endpoint.
    """

    def test_pep8_conformance_test_csv_to_json(self):
        """Test that test_validate_csv conforms to PEP8."""
        pep8s = pep8.StyleGuide(quiet=True)
        result = pep8s.check_files(['tests/test_validate_csv.py'])
        self.assertEqual(result.total_errors, 0, "Found code style errors" +
                         " (and warnings).")


class TestValidateCSV(unittest.TestCase):
    def setUp(self):
        """Set up for validate-csv tests"""
        self.base_url = 'http://localhost:5000/api/v1'

    @parameterized.expand([
        ("datasets/valid-csv-1.csv",),
        ("datasets/valid-csv-2.csv",),
        ("datasets/valid-csv-3.csv",)
    ])
    def test_with_valid_file(self, path):
        """
        Test that the correct success message is returned when a valid
        file is processed.
        """
        endpoint = self.base_url + '/validate-csv'

        with open(path, 'rb') as file:
            response = requests.post(endpoint, files={'file': file})

        # Assert the response status code and message
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'],
                         'CSV file received and validated successfully')

    def test_with_missing_file(self):
        """
        Test that an appropriate error is raised when a required file is
        missing.
        """
        endpoint = self.base_url + '/validate-csv'
        response = requests.post(endpoint)

        # Assert the response status code and error message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()['error'], 'No file found in the request. ' +
            'Please include a file in the \'file\' field.')

    @parameterized.expand([
        ('datasets/file.txt',),
        ('datasets/fdata-1.json',)
    ])
    def test_with_invalid_file_extension(self, path):
        """
        Test that an appropriate error is raised when a file with an
        invalid extension is used.
        """
        endpoint = self.base_url + '/validate-csv'
        with open(path, 'rb') as file:
            response = requests.post(endpoint, files={'file': file})
        # Assert the response status code and error message
        if path == 'datasets/file.txt':
            extension = 'txt'
        else:
            extension = 'json'
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()['error'], 'Invalid file type. The uploaded ' +
            f'file has a \'{extension}\' extension. ' +
            'Only CSV files are supported.')

    @parameterized.expand([
        ('datasets/invalid-csv-1.csv',),
        ('datasets/invalid-csv-2.csv',)
    ])
    def test_with_invalid_row_length(self, path):
        """
        Test that an appropriate error is raised when rows in a file have
        non-uniform lengths.
        """
        endpoint = self.base_url + '/validate-csv'
        with open(path, 'rb') as file:
            response = requests.post(endpoint, files={'file': file})

        if path == 'datasets/invalid-csv-1.csv':
            line_number = 12300
        else:
            line_number = 19419

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()['error'], 'Invalid CSV file. The length of each' +
            f' row should be consistent. Error at line {line_number}.')

    @parameterized.expand([
        ('datasets/missing-value-1.csv',),
        ('datasets/missing-value-2.csv',)
    ])
    def test_with_missing_values(self, path):
        """Test that no missing values are found in the file."""
        endpoint = self.base_url + '/validate-csv'

        with open(path, 'rb') as file:
            response = requests.post(endpoint, files={'file': file})

        if path == 'datasets/missing-value-1.csv':
            line_number = 2024
            header = 'Count'
        else:
            line_number = 19392
            header = "Child's First Name"
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()['error'], 'Invalid CSV file. Missing value ' +
            f'found at line {line_number}, Column {header}.')

    @parameterized.expand([
        ('datasets/data-type-1.csv',),
        ('datasets/data-type-2.csv',)
    ])
    def test_data_type_validation(self, path):
        """Test that each column in the file has a uniform data type."""
        endpoint = self.base_url + '/validate-csv'

        with open(path, 'rb') as file:
            response = requests.post(endpoint, files={'file': file})

        if path == 'datasets/data-type-1.csv':
            line_number = 500
            value = 'ALX'
            column_data_type = type(500)
        else:
            line_number = 1000
            value = 1216
            column_data_type = type('gender')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()['error'], "Invalid CSV file. Each column " +
            f"should have consistent datatype. Error at line {line_number}." +
            f" Value '{value}' is not of type '{column_data_type}'.")


if __name__ == '__main__':
    unittest.main()
