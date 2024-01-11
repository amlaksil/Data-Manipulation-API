# Data Manipulation API

The Data Manipulation API is a web-based application programming interface (API) designed to provide users with a set of endpoints to manipulate and process data in various formats. This API enables developers to perform common data manipulation tasks such as validating CSV files, transforming JSON data, transforming CSV file, merging CSV files, filtering JSON data, and more.

## Introduction

Working with data in its various formats is a fundamental aspect of understanding and harnessing the power of machine learning and analytics. CSV (Comma-Separated Values) and JSON (JavaScript Object Notation) are two widely used data formats, each with its unique characteristics and benefits. Driven by my passion for delving into the intricacies of data manipulation and my desire to simplify and expedite the process, I embarked on the journey of building a Data Manipulation API.

The inspiration for this project arose from my deep fascination with the potential of CSV and JSON data. Recognizing the importance of being comfortable and proficient in working with these formats, I set out to create a tool that would facilitate seamless and efficient data manipulation. I was motivated by the desire to empower others to dive into the depths of data, leveraging its insights to drive informed decision-making.

One of the primary objectives of the Data Manipulation API is to significantly reduce the time and complexity involved in validating CSV files. By implementing robust validation checks, such as identifying missing values and ensuring correct data types, the API streamlines the data validation process. This functionality not only saves valuable time but also enhances data reliability and integrity.

Furthermore, the API enables effortless transformation between CSV and JSON formats. Users can easily convert CSV files to JSON and vice versa, providing flexibility in data interchange. This feature promotes smooth integration between different systems and simplifies the data transformation process.

Throughout the development process, I immersed myself in various resources, tutorials, and documentation to enhance my understanding of data manipulation techniques. Exploring the powerful capabilities of libraries such as pandas, csv, and tempfile, I learned to effectively store and process data. This experience demanded patience, persistence, and an unwavering willingness to learn and adapt.

In Conclusion, the Data Manipulation API represents the culmination of my passion for working with data and my commitment to simplifying and enhancing the data manipulation experience. By creating a tool that enables seamless validation, merging, transformation, and filtering of CSV and JSON data, I hope to empower others in their journey to unravel the insights hidden within their datasets. Join me on this exciting adventure as we unlock the true potential of data and harness its power for informed decision-making.

## Features

1. Validation: The API allows users to validate CSV files, ensuring data integrity and reliability. It performs checks for missing values, data types, and other common validation criteria, providing users with feedback on potential issues and errors.

2. Merging: Users can merge multiple CSV files, combining data from different sources into a single comprehensive dataset. This feature enables better analysis and decision-making by providing a unified view of disparate data.

3. Transformation: The API supports seamless conversion between CSV and JSON formats, providing flexibility in data interchange. Users can easily transform data from one format to another, simplifying data integration processes.

4. Filtering: One of the key functionalities of the API is the ability to filter JSON data based on user-defined criteria. This empowers users to extract specific subsets of data from large JSON files, enabling targeted analysis and exploration.

5. Authentication: In order to ensure the utmost security and confidentiality of the data being manipulated, the Data Manipulation API incorporates JSON Web Token (JWT) authentication. The utilization of JWT authentication not only enhances data security but also offers benefits such as statelessness and scalability. The API does not need to store session information, resulting in improved performance and the ability to handle a larger number of concurrent requests without introducing complexity or compromising efficiency.

## Requirements

Before using the Data Manipulation API, please ensure that you have the following dependencies installed on your system. You can find installation instructions on their respective websites or install them using the provided command:
```
$ pip3 install -r requirements.txt
```
- Flask: [Flask Documentation](https://flask.palletsprojects.com/en/3.0.x/)
- Flask-Cors: [Flask-Cors Documentation](https://flask-cors.readthedocs.io/en/latest/)
- Jinja2: [Jinja2 Documentation](https://jinja.palletsprojects.com/en/3.1.x/)
- requests: [Requests Documentation](https://requests.readthedocs.io/en/latest/)
- pycodestyle: [pycodestyle Documentaion](https://pycodestyle.pycqa.org/en/latest/)
- pandas: [pandas Documentation](https://pandas.pydata.org/)
- Flask-SQLAlchemy: [Flask-SQLAlchemy Documentation](https://flask-sqlalchemy.palletsprojects.com/en/3.1.x/)
- Jwt: [PyJWT Documentation](https://pyjwt.readthedocs.io/en/stable/)

## Installation

1. Clone the repository to your local machine.
```
$ https://github.com/amlaksil/Data-Manipulation-API
```
2. Navigate to the project directory.
```
$ cd Data-Manipulation-API
```
3. Compile the code.
```
$ python3 -m api.v1.app
```
4. Make request. Example to validate csv file.
```bash
curl -X POST -F "file=@/path/to/your/file.csv" http://localhost:5000/api/v1/validate-csv
```

## Data Manipulation Endpoints

Offers various functionalities for working with CSV and JSON data, including CSV validation, CSV merging, CSV-to-JSON transformation, JSON-to-CSV transformation, and JSON filtering. Those endpoints utilizes the csv and pandas libraries for efficient handling and manipulation of CSV and JSON data. Additionally, they leverages the tempfile module to temporarily store files during the data manipulation processes.

### Validate CSV

- **Method:** POST
- **Endpoint:** `/validate-csv`

The `/validate-csv` endpoint checks the structure and data integrity of a CSV file. It ensures that the CSV file has consistent column lengths, no missing values, and consistent data types for each column throughout the file.

To use this endpoint, send a POST request with a file attachment containing the CSV data. The endpoint performs several validations, including verifying the file extension, validating file size, parsing and validating the CSV content, and checking the data types of individual cells. If the CSV file passes all the validations, a success message is returned. Otherwise, appropriate error messages are provided.

**Example:**
```bash
curl -X POST -F "file=@/path/to/your/file.csv" http://localhost:5000/api/v1/validate-csv
```

### Merge CSVS

- **Method:** POST
- **Endpoint:** `/merge-csvs`

The `/merge-csv` endpoint allows you to merge multiple CSV files into a single CSV file based on a specified merging technique. It expects a POST request with multiple file attachments containing the CSV files to be merged. The merging technique can be specified as an optional query parameter (technique), with the default value set to "inner".

After saving the uploaded CSV files to temporary locations, the endpoint merges them using the specified technique. If the merging is successful, the merged CSV file is returned as a downloadable file in the response. If any errors occur during the merging process, appropriate error messages are returned.

**Example:**
```bash
curl -X POST -H 'access-token: <token> -F "files=@/path/f1.csv" -F "files=@/path/f2.csv" http://localhost:5000/api/v1/merge-csvs?technique=<inner>
```

### CSV to JSON Transformation

- **Method:** POST
- **Endpoint:** `/csv-to-json`

The `/csv-to-json` endpoint allows you to convert a CSV file to JSON format. Each row in the CSV file is converted into a Python dictionary object and returned as a list of dictionaries in the JSON response.

To use this endpoint, send a POST request with a file attachment containing the CSV file you want to convert. The endpoint reads the CSV file, validates its format, and converts it to JSON format. Each row in the CSV is transformed into a Python dictionary, where the column names are used as keys and the corresponding row values are dictionary values.

**Example:**
```bash
curl -X POST -H 'access-token: <token> -F "file=@/path/to/your/file1.csv" http://localhost:5000/api/v1/csv-to-json
```

### JSON to CSV Transformation

- **Method:** POST
- **Endpoint:** `/json-to-csv`

The `/json-to-csv` endpoint allows you to convert JSON data to CSV format. You can either send JSON data in the request body or upload a JSON file as an attachment. The endpoint parses the JSON data and converts it to CSV format.

When sending JSON data in the request body, set the `Content-Type` header to `application/json`. Alternatively, when using a file attachment, set the `Content-Type` header to `multipart/form-data` and provide the JSON file using the key file.

If the conversion is successful, the JSON data is converted to a pandas DataFrame, and a CSV file is generated from the DataFrame. The generated CSV file is returned as a response attachment with the filename `output.csv`.

**Example:**
```bash
$ curl -X POST -H 'access-token: <token> -F "file=@/path/to/your/file.json" http://localhost:5000/api/v1/json-to-csv
```

### JSON Filter

- **Method:** POST
- **Endpoint:** `/json-filter`

The `/json-filter` endpoint allows you to filter JSON data based on criteria provided in the request payload. You can provide the filter criteria in the request header as JSON data.

To filter JSON data, send a POST request to the endpoint with the JSON data or file attachment. The filter criteria should be specified as a dictionary with keys representing field names and values representing the filtering conditions.

The endpoint applies the filter criteria to the data and returns the filtered data. Pagination is supported, and you can specify the page number and limit as query parameters in the URL.

**Request Header:**
- `Content-Type: application/json`
- `criteria: {"Field": {"operator": "value"}}`

Supported operators include:
- `eq` (Equal)
- `ne` (Not equal)
- `gt` (Greater than)
- `lt` (Less than)
- `gte` (Greater than or equal to)
- `lte` (Less than or equal to)

**Example:**
```bash
curl -X POST -H "Content-Type: application/json" -H 'criteria: {"Field": {"lte": value}}' -F "file=@/path/to/your/file.json" http://localhost:5000/api/v1/json-filter?page=<page_number>&limit=<limit_per_page>
```

## User Management Endpoints

In addition to the data manipulation endpoints, the API also provides user management endpoints defined in the `user.py` module. These endpoints allow creating, retrieving, and managing users. The following endpoints are available:

### Create User

- **Method:** POST
- **Endpoint:** `/user`

The `/user` endpoint allows you to create a new user by providing their name, password, and email in the request body. The user information should be included as fields in a JSON object.

To create a new user, send a POST request to the `/user` endpoint with the user's information in the request body. The endpoint validates the provided information and creates a new user account if the validation is successful. It returns a success message along with the newly created user object.

**Example:**
```bash
curl -XPOST -H "Content-Type: application/json" http://localhost:5000/api/v1/user -d '{"name": "Silamlak", "password": "a123", "email": "silamlak***@gmail.com"}'
```

### Login

- **Method:** GET
- **Endpoint:** `/login`

The `/login` endpoint allows you to authenticate a user and generate an access token. It requires basic authentication using the user's username and password.

To authenticate a user and generate an access token, send a GET request to the `/login` endpoint with the user's credentials. Include the username and password as the credentials in the request using the -u flag in `crl`. The endpoint validates the credentials and, if successful, returns an access token that can be used for subsequent authenticated requests.

**Example:**
```bash
$ curl -u <username>:<password> http://localhost:5000/api/v1/login
```

### Retrieve User

- **Method:** GET
- **Endpoint:** /user/<public_id>

The `/user/<public_id>` endpoint allows you to retrieve a specific user by their unique identifier (ID). Replace {id} in the endpoint URL with the ID of the user you want to retrieve.

To retrieve a user, send a GET request to the `/user/<public_id>` endpoint, where <public_id> is the ID of the user. The endpoint returns the user object containing their name, password, email, and other relevant information.

**Example:**
```bash
curl -XPOST http://localhost:5000/api/v1/user/<public_id>
```

### Delete USer

- **Method:** DELETE
- **Endpoint:** `/user/<public_id>`

The `/user/<public_id>` endpoint allows you to delete a specific user by their ID. Replace <public_id> in the endpoint URL with the ID of the user you want to delete. This endpoint requires authentication using an access token. Include the access token in the request header as the value for the `access-token` field.

To delete a user, send a DELETE request to the `/user/<public_id>` endpoint with the access token included in the request header. The endpoint removes the user from the system and returns a success message.

**Example:**
```bash
$ curl -XDELETE http://localhost:5000/api/v1/user/<public_id>
```

### Retrieve All Users

- **Method:** GET
- **Endpoint:** `/users`

The `/users` endpoint allows you to retrieve all users from the database. This endpoint requires authentication using an access token. Include the access token in the request header as the value for the `access-token` field.

To retrieve all users, send a GET request to the `/users` endpoint with the access token included in the request header. The endpoint validates the access token and, if successful, returns a list of user objects, each containing their name, password, email, and other relevant information.

**Example:**
```bash
curl -XPOST -H "access-token: <token>" http://localhost:5000/api/v1/users
```

### Delete All User

- **Method:** DELETE
- **Endpoint:** `/users/delete-all`

The `/users/delete-all` endpoint allows you to delete all users from the database. This endpoint requires authentication using an access token. Include the access token in the request header as the value for the `access-token` field.

To delete all users, send a DELETE request to the `/users/delete-all` endpoint with the access token included in the request header. The endpoint validates the access token and, if successful, returns a success message.

## Development

- If you'd like to contribute to the project, feel free to fork the repository and submit pull requests with your changes.
- Make sure to follow the coding style and conventions used in the existing codebase.

## Troubleshooting

- If you encounter any issues or have questions, please open an issue on the project's GitHub repository (https://github.com/amlaksil/Data-Manipulation-API/issues).

## Author

- [Silamlak Desye](https://www.linkedin.com/in/silamlakdesye)

Feel free to connect with me on LinkedIn for any questions, collaboration opportunities, or to learn more about my professional background.

## License

This project is licensed under the [MIT License](https://mit-license.org/amlaksil). See the [LICENSE](LICENSE) file for more details.
