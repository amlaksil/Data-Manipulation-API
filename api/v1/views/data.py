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
from datetime import datetime

from flask import jsonify, request, current_app, send_file, Response
from werkzeug.utils import secure_filename
import pandas as pd

from api.v1.views import app_views
from api.v1.views.user import token_required


def type_cast(value):
    """
    Tries to convert the given value into an integer, float, boolean, date,
    time, percentage, or None, and returns the converted value. If the
    conversion fails, the original value is returned.

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

    if value.lower() == "true":
        return True
    elif value.lower() == "false":
        return False

    try:
        # Date format: "YYYY-MM-DD"
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        pass

    try:
        return datetime.strptime(value, "%H:%M:%S")  # Time format: "HH:MM:SS"
    except ValueError:
        pass

    try:
        # Date and time format: "YYYY-MM-DD HH:MM:SS"
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        pass

    if value == "":
        return None

    if value.endswith("%"):
        try:
            return float(value[:-1]) / 100  # Percentage format: "X%"
        except ValueError:
            pass

    try:
        return float(value)  # Scientific notation format
    except ValueError:
        pass

    if value.lower() == "na" or value.lower() == "unknown":
        return None

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

    if not common_columns and technique is not 'inner':
        merged_df = pd.concat(dfs, ignore_index=True)
    else:
        if common_columns == set(df.columns):
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

    Returns: Success message if the file is validated successfully.
        If not appropriate error message is returned instead.
       - 400 Bad Request: If the server cannot process the request due to
            client error.

    Example Usage:
        curl -X POST -F "file=@/path/to/your/file.csv"
    http://localhost:5000/api/v1/validate-csv
    """
    # Check if a file is included in the request
    if 'file' not in request.files:
        return jsonify({'error': 'No file found in the request.' +
                        " Please include a file in the 'file' field."}), 400

    file = request.files['file']

    # Check if the file has a supported extension
    if file.filename == '' or not file.filename.endswith('.csv'):
        file_extension = file.filename.rsplit(".", 1)[-1]
        error_message = "Invalid file type. The uploaded file has a '" +\
            file_extension + "' extension. Only CSV files are supported."
        return jsonify({'error': error_message}), 400

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
            line_number = 2
            # Validate each row iteratively
            for row in reader:
                if len(row) != num_columns:
                    error_message = 'Invalid CSV file. The length of each ' +\
                        'row should be consistent. Error at line ' +\
                        f'{line_number}.'
                    return jsonify({'error': error_message}), 400

                for i, cell in enumerate(row):
                    cell = cell.strip()

                    # Check for missing values
                    if cell == '':
                        error_message = 'Invalid CSV file. Missing value ' +\
                            f'found at line {line_number}, Column ' +\
                            f'{header[i]}.'
                        return jsonify({'error': error_message}), 400

                    # Set the data type for the column if not set
                    if column_data_types[i] is None:
                        type_of_cell = type(type_cast(cell))
                        column_data_types[i] = type_of_cell

                    # Perform data type validation
                    value = type_cast(cell)
                    if not isinstance(value, column_data_types[i]):
                        error_message = 'Invalid CSV file. Each column ' +\
                            'should have consistent datatype. Error at line' +\
                            f" {line_number}. Value '{value}' is not of " +\
                            f"type '{column_data_types[i]}'."
                        return jsonify({'error': error_message}), 400
                line_number += 1

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
        - 400 Bad Request: If the server cannot process the request due to
              client error.

    Example Usage:
        curl -X POST -H 'access-token: <token>
    -F "files=@/path/to/your/file1.csv" -F "files=@/path/f2.csv"
    http://localhost:5000/api/v1/merge-csvs?technique=<inner>
    """
    # Check if files were uploaded
    if 'files' not in request.files:
        error_message = 'No file found in the request. Please include files' +\
            " in the 'files' field."
        return jsonify({'error': error_message}), 400

    files = request.files.getlist('files')
    technique = request.args.get('technique', 'inner')
    if len(files) < 2:
        error_message = "You should include at least two files to continue " +\
            "merging."
        return jsonify({'error': error_message}), 400

    # Save the uploaded files to temporary locations
    saved_files = []
    for file in files:
        if file and file.filename.endswith('.csv'):
            _, file_path = tempfile.mkstemp(suffix=".csv")
            file.save(file_path)
            saved_files.append(file_path)
        else:
            file_extension = file.filename.rsplit(".", 1)[-1]
            error_message = "Invalid file type. The uploaded " +\
                f"{file.filename} has a '" + file_extension + "' extension." +\
                " Only CSV files are supported."
            return jsonify({'error': error_message}), 400

    merged_temp_file = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
    try:
        merged_df = merge_csv_files(saved_files, technique)

        # Generate a unique filename for the merged CSV
        merged_filename = secure_filename('merged.csv')

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
        - 400 Bad Request: If the server cannot process the request due to
            client error.
        - 500 Internal Server Error: If an error occurs during the conversion
            process.

    Example Usage: curl -X POST -H 'access-token: <token>
    -F "file=@/path/to/your/file1.csv"
    http://localhost:5000/api/v1/csv-to-json
    """
    # Check if `file` is present in the request
    if 'file' not in request.files:
        error_message = 'No file found in the request. Please ' +\
            "include a file in the 'file' field."
        return jsonify({'error': error_message}), 400

    csv_file = request.files['file']

    # Check if the file has a supported extension
    if not csv_file.filename.endswith('.csv'):
        file_extension = csv_file.filename.rsplit(".", 1)[-1]
        error_message = "Invalid file type. The uploaded file has a '" +\
            file_extension + "' extension. Only CSV files are supported."
        return jsonify({'error': error_message}), 400

    # Read the CSV file using pandas
    try:
        df = pd.read_csv(csv_file)
    except Exception as e:
        return jsonify({'error': f'While reading the CSV file: {str(e)}'}), 400

    try:
        # Convert DataFrame to JSON
        json_data = df.to_dict(orient='records')
    except Exception as e:
        return jsonify({'error': f'While parsing to dict: {str(e)}'}), 400

    return Response(
        json.dumps(json_data, indent=4) + '\n',
        status=200, mimetype='application/json')


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

    Example Usage: curl -X POST -H 'access-token: <token>
    -F "file=@/path/to/your/file.json"
    http://localhost:5000/api/v1/json-to-csv
    """
    content_type = request.headers.get('Content-Type')
    if content_type == 'application/json':
        try:
            if type(request.json) is dict:
                json_data = request.json['data']
            else:
                if not request.data:
                    return jsonify(
                        {'error': 'No data is provided in the request'}), 400
                json_data = request.json
        except Exception as e:
            return jsonify(
                {'error', 'Failed to parse JSON data: ' + str(e)}), 400
    elif content_type is not None and\
            request.headers.get('Content-Type').startswith(
                'multipart/form-data'):
        if 'file' in request.files:
            json_file = request.files['file']
            # Check if the file has a supported extension
            if not json_file.filename.endswith('.json'):
                file_extension = json_file.filename.rsplit(".", 1)[-1]
                error_message = "Invalid file type. The uploaded file has " +\
                    "a '" + file_extension + "' extension. Only JSON files " +\
                    "are supported."
                return jsonify({'error': error_message}), 400
            try:
                json_data = json.load(json_file)
                if type(json_data) is dict:
                    if 'data' in json_data:
                        json_data = json_data['data']
            except Exception as e:
                return jsonify(
                    {'error': 'Failed to read and parse JSON file: ' + str(e)}
                ), 400
        else:
            error_message = 'No file found in the request. Please include a' +\
                " file in the 'file' field."
            return jsonify({'error': error_message}), 400
    else:
        return jsonify(
            {'error': "Invalid Content-Type. Expected 'application/json'" +
             " or 'multipart/form-data'"}), 415
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
            {'error': 'Invalid JSON data.' +
             ' Expected a list of dictionaries.'}), 400

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


@app_views.route('/json-filter', methods=['POST'])
def json_filter():
    """
    Filter JSON data based on criteria provided in the request payload and
    perform pagination.

    Endpoint: POST /json-filter

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
        - 400 Bad Request: If the server cannot process the request due to
        client error.
        - 415 Unsupported Media Type: If the request does not have the expected
        Content-Type header.

    Example Usage: curl -X POST -H 'criteria: {"Age": {"lte": 30}}'
    -F "file=@/path/to/your/file.json"
    http://localhost:5000/api/v1/json-filter?
    page=<page_number>&limit=<limit_per_page>
    """
    content_type = request.headers.get('Content-Type')
    if content_type == 'application/json':
        try:
            if not request.data:
                return jsonify(
                    {'error': 'No data is provided in the request'}), 400
            data = request.json
        except Exception as e:
            return jsonify(
                {'error', 'Failed to parse JSON data: ' + str(e)}), 400
    elif content_type is not None and \
            request.headers.get('Content-Type').startswith(
                'multipart/form-data'):
        if 'file' in request.files:
            json_file = request.files['file']

            # Check if the file has a supported extension
            if not json_file.filename.endswith('.json'):
                file_extension = json_file.filename.rsplit(".", 1)[-1]
                error_message = "Invalid file type. The uploaded file has " +\
                    "a '" + file_extension + "' extension. Only JSON files " +\
                    "are supported."
                return jsonify({'error': error_message}), 400
            try:
                data = json.load(json_file)
            except Exception as e:
                return jsonify(
                    {'error': 'Failed to read and parse JSON file: ' +
                     str(e)}), 400
        else:
            error_message = 'No file found in the request. Please include ' +\
                "a file in the 'file' field."
            return jsonify({'error': error_message}), 400
    else:
        return jsonify({
            "error": "Invalid Content-Type. Expected 'application/json' or " +
            "'multipart/form-data'"
        }), 415

    if data is None or not data:
        return jsonify({'error': 'No data is provided'}), 400
    if isinstance(data, list):
        data = {'data': data}

    if 'criteria' not in request.headers:
        return jsonify({'error': 'You must set a filter criteria before ' +
                        'starting the filtering process.'}), 400

    # Retrieve the filter criteria from the header
    criteria_header = request.headers.get('criteria')
    try:
        criteria = json.loads(criteria_header) if criteria_header else {}
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid JSON format in criteria header. ' +
                        'It should be dictionary object.'}), 400

    if not isinstance(criteria, dict):
        return jsonify(
            {'error': 'The criteria should be dictionary object.'}), 400

    values = list(criteria.values())
    if len(values) == 0:
        return jsonify(
            {'error': "Empty criteria or dictionary: 'criteria: {}'"}), 400
    if not isinstance(values[0], dict):
        return jsonify(
            {'error': "The 'criteria' value should be in the following" +
             " format: '<criteria>: {<key> : {<operator>: "
             "<value to be compared>}}'. Example: " +
             'criteria: {"Age": {"gt": 18}}'}), 400

    operator = list(values[0].keys())
    if len(operator) == 0:
        return jsonify(
            {'error': "key without operator 'criteria: {'key': {}}'"}), 400
    print('operator used=', operator)
    if operator[0] not in ['eq', 'ne', 'gt', 'lt', 'gte', 'lte']:
        return jsonify(
            {'error': 'You have used invalid operator. Please ' +
             "use one of the following instead:" +
             " ['eq, 'ne', 'gt', 'lt', 'gte', 'lte']"}), 400

    # Apply the filter criteria to the data
    try:
        filtered_data = [
            item
            for item in data['data']
            if all(
                key in item and compare_values(item[key], operator, value)
                for key, filter_ in criteria.items()
                for operator, value in filter_.items()
            )
        ]
    except Exception as e:
        return jsonify(
            {'error': 'An Error occurred while filtering data: ' +
             str(e)}), 400

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

    return Response(
        json.dumps(response, indent=4) + '\n',
        status=200, mimetype='application/json')


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
