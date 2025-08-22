import mimetypes

import boto3
from django.conf import settings
from rest_framework import status
from rest_framework.exceptions import APIException


class S3UploadError(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "An error occurred while uploading your image to AWS"
    default_code = "aws_upload_error"


class S3DeleteError(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "An error occurred while deleting the image from AWS"
    default_code = "aws_delete_error"


s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_CONFIG.AWS_S3_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_CONFIG.AWS_S3_SECRET_ACCESS_KEY,
    region_name=settings.AWS_CONFIG.AWS_S3_REGION_NAME,
)


def upload_file_to_s3(file, file_path):
    try:
        # Move to the start of the file to ensure the whole file is read
        file.seek(0)

        # Guess the content type of the file
        content_type, _ = mimetypes.guess_type(file_path)
        content_type = (
            content_type or "application/octet-stream"
        )  # Fallback if type is unknown

        # Use put_object to upload the file content with ContentType
        response = s3_client.put_object(
            Bucket=settings.AWS_CONFIG.AWS_STORAGE_BUCKET_NAME,
            Key=file_path,
            Body=file,
            ContentType=content_type,
        )

        # Check for a successful response
        if response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 200:
            file_url = f"https://{settings.AWS_CONFIG.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{file_path}"
            return file_url
        else:
            print(f"Upload response: {response}")
            raise S3UploadError("Failed to upload file with put_object.")

    except Exception as e:
        # Handle upload error
        print(f"Upload failed: {e}")
        raise S3UploadError


s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_CONFIG.AWS_S3_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_CONFIG.AWS_S3_SECRET_ACCESS_KEY,
    region_name=settings.AWS_CONFIG.AWS_S3_REGION_NAME,
)


def delete_image_from_s3(file_path):
    try:
        response = s3_client.delete_object(
            Bucket=settings.AWS_CONFIG.AWS_STORAGE_BUCKET_NAME, Key=file_path
        )

        # Check if the deletion was successful
        if response.get("ResponseMetadata", {}).get("HTTPStatusCode") != 204:
            raise S3DeleteError("Failed to delete file.")
    except Exception as e:
        print(f"Deletion failed: {e}")
        raise S3DeleteError
