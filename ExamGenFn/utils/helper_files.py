import boto3
from botocore.exceptions import NoCredentialsError
from pdfminer.high_level import extract_text
from io import BytesIO
import io

import json
import csv

class HelperFiles:
    def __init__(self, bucket_name=None, file_key=None, file_object=None):
        """
        Initializes the HelperFiles with specified bucket and file key.

        :param bucket_name: Name of the S3 bucket.
        :param file_key: Key of the file in the S3 bucket.
        """
        self.bucket_name = bucket_name
        self.file_key = file_key
        self.file_object = file_object

    def get_pdf_text_local(self):
        """
        Retrieves a PDF file from a local path and extracts the text.

        :return: Extracted text from the PDF.
        """
        text = extract_text(self.file_key)
        return text
     
    def get_pdf_text_s3(self):
        """
        Retrieves a PDF file from an S3 bucket and extracts the text.

        :return: Extracted text from the PDF.
        """
        try:
            # Create a new S3 client instance
            s3 = boto3.client('s3')

            # Use boto3 to get the file from S3
            response = s3.get_object(Bucket=self.bucket_name, Key=self.file_key)
            file_content = response['Body'].read()

            # Use BytesIO to create a file-like object from the file content
            with BytesIO(file_content) as pdf_file:
                # Use pdfminer's extract_text function on the file-like object
                text = extract_text(pdf_file)

            return text

        except boto3.exceptions.Boto3Error as e:
            print(f"An error occurred while accessing S3: {e}")
            return None  # or handle the error as appropriate for your application

    def get_pdfobject_text(self):
        """
        extracts the text from pdf file object.
        
        :return: Extracted text from the PDF.
        """
        try:
            # Use BytesIO to create a file-like object from the file content
            with BytesIO(self.file_object) as pdf_file:
                # Use pdfminer's extract_text function on the file-like object
                text = extract_text(pdf_file)
            return text

        except boto3.exceptions.Boto3Error as e:
            print(f"An error occurred while accessing S3: {e}")
            return None

    def convert_to_csv_in_memory(self, text):
        """
        Convert list text to CSV and store it in memory.

        :param text: JSON text to be converted.
        :return: File-like object containing CSV data.
        """
        # Parse the JSON string to convert it into a Python object (list of dictionaries)
        start_index = text.find('[')  # Find the index where JSON starts
        json_string = text[start_index:].strip("```")  # Substring from start_index to the end
        data_list = json.loads(json_string)

        # Create an in-memory text stream (this will hold the CSV data)
        output = io.StringIO()

        # Create a CSV writer object configured to write to the in-memory text stream
        writer = csv.writer(output)

        # Determine the maximum number of options in any question
        max_options = max(len(item['options']) for item in data_list)

        # Prepare the header based on the maximum number of options
        header = ["Question"] + [f"Option {chr(65+i)}" for i in range(max_options)] + ["Correct Answer"]
        writer.writerow(header)

        # Write the data rows
        for item in data_list:
            question = item['question']
            options = item['options']
            correct_answer = item['correct_answer']

            # Make sure all rows have the same number of columns
            row = [question] + options + [''] * (max_options - len(options)) + [correct_answer]

            # Write the current row
            writer.writerow(row)

        # To ensure the content is in the buffer, seek the pointer back to the start of the stream
        output.seek(0)

        # The 'output' object now contains the CSV data in memory
        return output

    def convert_to_json_in_memory(self, text):
        """
        Keep the JSON text and store it in memory.

        :param text: JSON text to be stored.
        :return: File-like object containing JSON data.
        """
        # Parse the JSON string to ensure it's valid JSON and to convert it into a Python object
        start_index = text.find('[')  # Find the index where JSON starts
        json_string = text[start_index:].strip("```")  # Substring from start_index to the end, removing any extra characters
        data_list = json.loads(json_string)  # This also validates the JSON content

        # Create an in-memory text stream (this will hold the JSON data)
        output = io.StringIO()
    
        # Write the JSON data to the in-memory stream
        json.dump(data_list, output)

        # To ensure the content is in the buffer, seek the pointer back to the start of the stream
        output.seek(0)

        # The 'output' object now contains the JSON data in memory
        return output
    def upload_to_s3(self, file_obj, bucket_name, s3_file_path):
        """
        Upload a file-like object to an S3 bucket.

        :param file_obj: File-like object to upload (must support 'read()' method).
        :param bucket_name: Name of the S3 bucket.
        :param s3_file_path: The file path in the S3 bucket (e.g., 'folder/filename.csv').
        """
        # Create an S3 client
        s3 = boto3.client('s3')

        try:
            # Check if the file object is a string-based file-like object (e.g., StringIO)
            # and convert it to a byte-based file-like object (e.g., BytesIO) if necessary.
            if isinstance(file_obj, io.StringIO):
                # Convert string data to bytes
                file_obj_bytes = io.BytesIO(file_obj.getvalue().encode())
            else:
                # If it's already a BytesIO instance, we don't need to convert
                file_obj_bytes = file_obj

            # Ensure the pointer is at the start of the file-like object
            file_obj_bytes.seek(0)

            # Upload the file-like object to S3
            print("file path in helper="+ s3_file_path)
            s3.upload_fileobj(file_obj_bytes, bucket_name, s3_file_path)
            print(f"File uploaded to {bucket_name}/{s3_file_path}")
        except Exception as e:
            print(f"An error occurred uploading to s3: {e}")