#!/usr/bin/python3

"""
This module provides a collection of routes for a data manipulation API. It
offers various functionalities for working with CSV and JSON data, including
CSV validation, CSV merging, CSV-to-JSON conversion, JSON-to-CSV conversion,
and JSON filtering. The module utilizes the csv and pandas libraries for
efficient handling and manipulation of CSV and JSON data. Additionally, it
leverages the tempfile module to temporarily store files during the data
manipulation processes.
"""
import csv
import io
import json
import os
import tempfile

from flask import jsonify, request, current_app, send_file, Response
from werkzeug.utils import secure_filename
import pandas as pd

from api.v1.views import app_views
from api.v1.views.user import token_required


def type_cast(value):
    """
    Tries to convert the given value into an integer or float, and returns
    the converted value. If the conversion fails, the original value is
    returned

    Args:
        value: The value to be typecasted.

    Returns:
        The converted value if successful, otherwise the original value.
    """
    try:
        return int(value)
    except ValueError:
        pass

    try:
        return float(value)
    except ValueError:
        pass

    return value


def merge_csv_files(csv_files, technique):
    """
    Merge multiple CSV files into a single DataFrame.

    Args:
        csv_files (list[str]): A list of file paths for the CSV files
            to be merged.
        technique (str): The merging technique to be applied when the CSV
            files have different headers.
            - If the files have the same headers, "concat" concatenates
        the rows vertically while preserving the header.
            - If the files have different headers, "merge" merges the files
        based on a common set of columns.

    Returns:
        pandas.DataFrame: The merged DataFrame containing the combined data
    from the input CSV files.

    Raises:
        ValueError: If the provided list of CSV files is empty.

    Notes:
        - The function assumes that the CSV files have a header row.
        - The merging technique determines how the files with different
            headers are combined.
            - "inner": Only the common columns between the files are retained.
            - "outer": All columns from all files are retained, with missing
                values filled with NaN.
            - "left": All columns from the left file are retained, with missing
                values filled with NaN.
            - "right": All columns from the right file are retained, with
                missing values filled with NaN.
    Example:
        csv_files = ["file1.csv", "file2.csv", "file3.csv"]
        merged_data = merge_csv_files(csv_files, technique="merge")
    """
    dfs = []
    common_columns = None

    for file in csv_files:
        df = pd.read_csv(file)
        if common_columns is None:
            common_columns = set(df.columns)
        else:
            common_columns = common_columns.intersection(df.columns)
        dfs.append(df)

    if not common_columns:
        merged_df = pd.concat(dfs, ignore_index=True)
    else:
        if len(common_columns) == len(df.columns):
            """If the file has the same headers. In thiscase, we can
            simply use pd.concat with axis=0 to concatenate the rows
            vertically while preserving the header."""
            merged_df = pd.concat(dfs, axis=0, ignore_index=True)
        else:
            merged_df = dfs[0]
            for df in dfs[1:]:
                merged_df = pd.merge(merged_df, df, on=list(
                    common_columns), how=technique)
    return merged_df


@app_views.route('/validate-csv', methods=['POST'])
def validate_csv():
    """
    Checks the structure and data integrity of a CSV file. It ensures that the
    CSV file has consistent column lengths, no missing values, and consistent
    data types for each column throughout the file.

    Returns:
        A JSON response with either a success message or an error message.

    Endpoint: /api/v1/validate-csv
    Method: POST

    Request Parameters:
        - file: The CSV file to be validated (multipart/form-data)

    Returns:
        - If the CSV file is valid, returns a JSON response with a
                success message:
          {
              "message": "CSV file received and validated successfully"
          }

        - If the request is missing the file or the file has an unsupported
                extension, returns a JSON error message:
          {
              "error": "No file included in the request"
          }
          or
          {
              "error": "Invalid file. Only CSV files are supported."
          }

        - If the CSV file is invalid (e.g., incorrect formatting, missing\
                columns, or invalid data), returns a JSON error message:
          {
              "error": "Invalid CSV file"
          }

    Example Usage:
        curl -X POST -F "file=@/path/to/your/file.csv"
    http://localhost:5000/api/v1/validate-csv
    """
    # Check if a file is included in the request
    if 'file' not in request.files:
        return jsonify({'error': 'No file included in the request'}), 400

    file = request.files['file']

    # Check if the file has a supported extension
    if file.filename == '' or not file.filename.endswith('.csv'):
        return jsonify(
            {'error': 'Invalid file. Only CSV files are supported.'}), 400

    # Check the file size against the limit
    if file and file.content_length > current_app.config['MAX_CONTENT_LENGTH']:
        return jsonify(
            {'error': 'File size exceeds the limit. Please upload a file' +
             'smaller than 10 megabytes.'}), 400

    try:
        # Save the file to a temporary location
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, file.filename)
        file.save(temp_file_path)

        with open(temp_file_path, 'r', encoding='utf-8') as file_data:
            reader = csv.reader(file_data, delimiter=',')

            # Read and validate the header row
            header = next(reader)
            num_columns = len(header)

            # Keep track of column data types
            column_data_types = [None] * num_columns

            # Validate each row iteratively
            for row in reader:
                if len(row) != num_columns:
                    return jsonify({'error': 'Invalid CSV file'}), 400

                for i, cell in enumerate(row):
                    cell = cell.strip()

                    # Check for missing values
                    if cell == '':
                        return jsonify({'error': 'Invalid CSV file'}), 400

                    # Set the data type for the column if not set
                    if column_data_types[i] is None:
                        type_of_cell = type(type_cast(cell))
                        column_data_types[i] = type_of_cell

                    # Perform data type validation
                    value = type_cast(cell)
                    if not isinstance(value, column_data_types[i]):
                        return jsonify({'error': 'Invalid CSV file'}), 400

        # Remove the temporary file
        os.remove(temp_file_path)
        return jsonify({'message':
                        'CSV file received and validated successfully'}), 200
    except csv.Error as e:
        return jsonify(
            {'error': f'Error while parsing the CSV file: {str(e)}'}), 400


@app_views.route('/merge-csvs', methods=['POST'])
@token_required
def merge_csvs(_):
    """
    Merge multiple CSV files into a single CSV file based on the specified
        merging technique.

    Endpoint: POST /merge-csv?technique={technique}

    Request Parameters:
        - files: List of CSV files to be merged. Attach each file using the
                key 'files'.
                (multipart/form-data)
        - technique (optional): The merging technique to be used. Default is
                'inner'. (query parameter)

    Responses:
        - 200 OK: If the CSV files are successfully merged, the merged CSV file
                is returned as a downloadable file.
        - 400 Bad Request: If any of the following conditions occur:
            - No files are uploaded.
            - No valid CSV files are uploaded.
            - An error occurs during the merging process.
    """
    # Check if files were uploaded
    if 'files' not in request.files:
        return jsonify({'error': 'No files were uploaded.'}), 400

    files = request.files.getlist('files')
    technique = request.args.get('technique', 'inner')

    # Save the uploaded files to temporary locations
    saved_files = []
    for file in files:
        if file and file.filename.endswith('.csv'):
            _, file_path = tempfile.mkstemp(suffix=".csv")
            file.save(file_path)
            saved_files.append(file_path)

    if not saved_files:
        return jsonify({'error': 'No valid CSV files were uploaded.'}), 400

    try:
        merged_df = merge_csv_files(saved_files, technique)

        # Generate a unique filename for the merged CSV
        merged_filename = secure_filename('merged.csv')

        # Save the merged DataFrame to a temporary file
        merged_temp_file = tempfile.NamedTemporaryFile(
            suffix=".csv", delete=False)
        merged_df.to_csv(merged_temp_file.name, index=False)
        merged_temp_file.close()

        # Return the merged CSV file has a downloadable file
        return send_file(
            merged_temp_file.name,
            as_attachment=True)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    finally:
        # Remove the temporary files
        for file_path in saved_files:
            os.remove(file_path)

        # Remove the merged temporary file
        os.remove(merged_temp_file.name)


@app_views.route('/csv-to-json', methods=['POST'])
@token_required
def csv_to_json(_):
    """
    Convert a CSV file to JSON format.

    Endpoint: POST /csv-to-json

    Request Parameters:
        - file: CSV file to be converted. Attach the file using the key 'file'.
                (multipart/form-data)

    Responses:
        - 200 OK: If the CSV file is successfully converted, the converted JSON
            data is returned as a list of dictionaries in the response body.
        - 400 Bad Request: If no file is present in the request or the uploaded
            file is not a valid CSV file.
        - 500 Internal Server Error: If an error occurs during the conversion
            process.
    """
    # Check if `file` is present in the request
    if 'file' not in request.files:
        return jsonify({'error': 'No file present in the request'}), 400
    csv_file = request.files['file']

    # if not file.filename.endswith('.csv'):
    # Read the CSV file using pandas
    try:
        df = pd.read_csv(csv_file)
    except pd.errors.ParseError as e:
        return jsonify({'error': 'Invalid CSV file format'}), 400

    try:
        # Convert DataFrame to JSON
        json_data = df.to_dict(orient='records')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'data': json_data}), 200


@app_views.route('/json-to-csv', methods=['POST'])
@token_required
def json_to_csv(_):
    """
    Convert JSON data to CSV format.

    Endpoint: POST /json-to-csv

    Request Parameters:
        - JSON data: The JSON data to be converted. Attach the data as a JSON
                object in the request body. (application/json)
        - JSON file: Alternatively, you can attach a JSON file to be converted.
                Attach the file using the key 'file'. (multipart/form-data)

    Responses:
        - 200 OK: If the JSON data is successfully converted to CSV, the
                converted CSV file is returned as a response attachment.
        - 400 Bad Request: If the request does not contain valid JSON data or
                file, or if the conversion process encounters an error.
        - 415 Unsupported Media Type: If the request does not have the expected
                Content-Type header.
    """
    # Check if 'data' is present in the request JSON
    # if 'data' in request.json:
    if request.headers.get('Content-Type') == 'application/json':
        try:
            json_data = request.json['data']
        except Exception as e:
            return jsonify(
                {'error', 'Failed to parse JSON data: ' + str(e)}), 400
    elif request.headers.get('Content-Type').startswith('multipart/form-data'):
        if 'file' in request.files:
            json_file = request.files['file']
            try:
                json_data = json.load(json_file)
                if 'data' in json_data:
                    json_data = json_data['data']
            except Exception as e:
                return jsonify(
                    {'error': 'Failed to read and parse JSON file: ' + str(e)}
                ), 400
        else:
            return jsonify(
                {'error': 'No JSON data or file present in the request'}), 400
    else:
        return jsonify(
            {'error': 'Invalid Content-Type. Expected "application/json" +\
            "or "multipart/form-data"'}), 415
    if isinstance(json_data, str):
        try:
            json_data = json.loads(json_data)
        except Exception as e:
            return jsonify(
                {'error': 'Failed to parse JSON data: ' + str(e)}), 400

    # Check if the JSON data is a list
    if not isinstance(json_data, list):
        return jsonify({'error': 'Invalid JSON data. Expected a list.'}), 400

    # Check if the list is empty
    if len(json_data) == 0:
        return jsonify({'error': 'Empty JSON array. No data to convert.'}), 400

    # Check if each element in the list is a dictionary
    if not all(isinstance(item, dict) for item in json_data):
        return jsonify(
            {'error': 'Invalid JSON data." +\
            "Expected a list of dictionaries.'}), 400

    # Convert JSON to DataFrame
    try:
        df = pd.DataFrame(json_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    csv_data = df.to_csv(index=False)
    response = Response(csv_data, mimetype='text/csv')
    response.headers.set('Content-Disposition',
                         'attachment', filename='output.csv')
    return response


@app_views.route('/filter-json', methods=['POST'])
def json_filter():
    """
    Filter JSON data based on criteria provided in the request payload and
    perform pagination.

    Endpoint: POST /filter-json

    Request Parameters:
        - JSON data: The JSON data to be filtered. Attach the data as a JSON
        object in the request body. (application/json)
        - JSON file: Alternatively, you can attach a JSON file to be filtered.
        Attach the file using the key 'file'. (multipart/form-data)
        - Pagination: You can specify the page number and limit as query
        parameters in the URL. (?page=<page_number>&limit=<limit_per_page>)

    Responses:
        - 200 OK: If the JSON data is successfully filtered and paginated, the
        filtered and paginated data is returned in the response body as a JSON
        object.
        - 400 Bad Request: If the request does not contain valid JSON data or
        file, or if the filtering process encounters an error.
        - 415 Unsupported Media Type: If the request does not have the expected
        Content-Type header.

    """
    # Get the payload and data file from the request
    if request.headers.get('Content-Type') == 'application/json':
        try:
            data = request.json
        except Exception as e:
            return jsonify(
                {'error', 'Failed to parse JSON data: ' + str(e)}), 400
    elif request.headers.get('Content-Type').startswith('multipart/form-data'):
        if 'file' in request.files:
            json_file = request.files['file']
            try:
                data = json.load(json_file)
            except Exception as e:
                return jsonify(
                    {'error': 'Failed to read and parse JSON file: ' +
                     str(e)}), 400
        else:
            return jsonify(
                {'error': 'No JSON data or file present in the request'}), 400
    else:
        return jsonify({
            'error': 'Invalid Content-Type. Expected "application/json" or' +
            '"multipart/form-data"'
            }), 415

    # Retrieve the filter criteria from the payload
    criteria = data.get('criteria', {})

    # Apply the filter criteria to the data
    filtered_data = [
        item
        for item in data['data']
        if all(
            key in item and compare_values(item[key], operator, value)
            for key, filter_ in criteria.items()
            for operator, value in filter_.items()
        )
    ]

    # Perform pagination on the filtered data
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    start_index = (page - 1) * limit
    end_index = start_index + limit
    paginated_data = filtered_data[start_index:end_index]

    # Prepare the response
    response = {
        'page': page,
        'total_pages': (len(filtered_data) + limit - 1) // limit,
        'total_records': len(filtered_data),
        'filtered_data': paginated_data
    }

    return jsonify(response)


def compare_values(item_value, operator, filter_value):
    """
    Compares two values based on the given operator and returns a
    boolean result.

    Args:
        item_value: The value to be compared.
        operator: The operator used for comparison. Valid options are:
                  'eq' (equal),
                  'ne' (not equal), 'gt' (greater than), 'lt' (less than),
                  'gte' (greater than or equal to), 'lte'
                      (less than or equal to).
        filter_value: The value to compare against.

    Returns:
        True if the comparison condition is satisfied; False otherwise.
    """
    if operator == "eq":
        return item_value == filter_value
    elif operator == "ne":
        return item_value != filter_value
    elif operator == "gt":
        return item_value > filter_value
    elif operator == "lt":
        return item_value < filter_value
    elif operator == "gte":
        return item_value >= filter_value
    elif operator == "lte":
        return item_value <= filter_value
    else:
        return False
