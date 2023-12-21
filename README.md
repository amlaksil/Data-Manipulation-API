# Data Manipulation API

The Data Manipulation API is a web-based application programming interface (API) designed to provide users with a set of endpoints to manipulate and process data in various formats. This API enables developers to perform common data manipulation tasks such as validating CSV files, transforming JSON data, merging CSV files, 
filtering JSON data, and more.

## Available Endpoints
- Validate CSV Method: POST
Endpoint: /api/v1/validate-csv
The validate-csv endpoint checks the structure and data integrity of a CSV file. It ensures that the CSV file has consistent column lengths, no missing values, and consistent data types for each column throughout the file.

To use this endpoint, send a POST request with a file attachment containing the CSV data. The endpoint performs several validations, including verifying the file extension, validating file size, parsing and validating the CSV content, and checking the data types of individual cells. If the CSV file passes all the validations, a success message is returned. Otherwise, appropriate error messages are provided.

- Merge CSV Method: PUT
Endpoint: /api/v1/merge-csv
The merge-csv endpoint allows you to merge multiple CSV files into a single CSV file based on a specified merging technique. It expects a POST request with multiple file attachments containing the CSV files to be merged. The merging technique can be specified as an optional query parameter (technique), with the default value set to "inner".

After saving the uploaded CSV files to temporary locations, the endpoint merges them using the specified technique. If the merging is successful, the merged CSV file is returned as a downloadable file in the response. If any errors occur during the merging process, appropriate error messages are returned.

- Convert CSV to JSON Method: POST
Endpoint: /api/v1/csv-to-json
The csv-to-json endpoint allows you to convert a CSV file to JSON format. Each row in the CSV file is converted into a Python dictionary object and returned as a list of dictionaries in the JSON response.

- Filter JSON Method: POST
Endpoint: /api/v1/json-filter
The json-filter endpoint allows you to filter JSON data based on criteria provided in the request payload. You can provide the filter criteria either in the request body as JSON data or by uploading a JSON file as an attachment.

To filter JSON data, send a POST request to the endpoint with the JSON data or file attachment. The filter criteria should be specified as a dictionary with keys representing field names and values representing the filtering conditions.

The endpoint applies the filter criteria to the data and returns the filtered data. Pagination is supported, and you can specify the page number and limit as query parameters in the URL.

## User Management Endpoints
In addition to the data manipulation endpoints, the API also provides user management endpoints defined in the user.py module. These endpoints allow creating, retrieving, and managing users. The following endpoints are available:

GET /api/v1/users: Retrieves a list of all users.
GET /api/v1/user/<public_id>: Retrieves a specific user by their public ID.
POST /api/v1/user: Creates a new user.
DELETE /api/v1/user/<public_id>: Deletes a specific user by their public ID.
POST /api/v1/login: Authenticates a user and generates an access token.
These endpoints enable user registration, authentication, and basic user management functionalities in the API.

## Development

- If you'd like to contribute to the project, feel free to fork the repository and submit pull requests with your changes.
- Make sure to follow the coding style and conventions used in the existing codebase.

## Troubleshooting

- If you encounter any issues or have questions, please open an issue on the project's GitHub repository (https://github.com/amlaksil/maze-project/issues).

## Author

- [Silamlak Desye](https://www.linkedin.com/in/silamlakdesye)

Feel free to connect with me on LinkedIn for any questions, collaboration opportunities, or to learn more about my professional background.

## License

This project is licensed under the [MIT License](https://mit-license.org/amlaksil). See the [LICENSE](LICENSE) file for more details.
