import imghdr
import uuid
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.shortcuts import get_object_or_404

from authentication.models import User
from media.features.image.models import Image, generate_upload_path
from services.s3_service import delete_image_from_s3


class ImageService:
    """
    Service class for handling image uploads, validations, and retrievals.
    """

    def __init__(
        self,
        s3_client: Optional[boto3.client] = None,
        bucket_name: Optional[str] = None,
    ):
        """
        Initialize S3 client with optional dependency injection for testing.

        Args:
            s3_client (boto3.client, optional): S3 client instance
            bucket_name (str, optional): S3 bucket name
        """
        self.s3_client = s3_client or boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_CONFIG.AWS_S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_CONFIG.AWS_S3_SECRET_ACCESS_KEY,
            region_name=settings.AWS_CONFIG.AWS_S3_REGION_NAME,
            endpoint_url="https://s3.af-south-1.amazonaws.com",
        )
        self.bucket_name = (
            bucket_name or settings.AWS_CONFIG.AWS_STORAGE_BUCKET_NAME
        )

    def validate_image(self, image: UploadedFile) -> bool:
        """
        Validate image based on multiple criteria.

        Args:
            image (UploadedFile): Uploaded image file

        Returns:
            bool: Whether image is valid
        """
        # Check file size (e.g., max 10MB)
        if image.size > 10 * 1024 * 1024:
            return False

        # Validate image type
        valid_types = ["jpeg", "png", "gif", "webp"]
        image_type = imghdr.what(image)

        return image_type in valid_types

    def generate_unique_filename(self, original_filename: str) -> str:
        """
        Generate a unique filename with UUID and original extension.

        Args:
            original_filename (str): Original uploaded filename

        Returns:
            str: Unique filename
        """
        extension = original_filename.split(".")[-1].lower()
        unique_filename = f"{uuid.uuid4()}.{extension}"
        return unique_filename

    def upload_image(
        self,
        image: UploadedFile,
        folder: str,
        uploaded_by: User,
    ) -> Dict[str, str]:
        """
        Upload single image to S3 with validation and unique naming.

        Args:
            image (UploadedFile): Image file to upload
            folder (str, optional): S3 folder path

        Returns:
            Dict[str, str]: Upload metadata
        """
        if not self.validate_image(image):
            raise ValueError("Invalid image file")

        unique_filename = self.generate_unique_filename(image.name)
        s3_key = f"{folder}{unique_filename}"

        try:
            self.s3_client.upload_fileobj(
                image,
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    "ContentType": image.content_type,
                    "ACL": "private",  # Secure by default
                },
            )
        except ClientError as e:
            raise RuntimeError(f"S3 Upload Error: {str(e)}")

        self.save_image_to_db(
            image_key=s3_key,
            uploaded_by=uploaded_by,
        )

        return {
            "url": f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}",
            "key": s3_key,
        }

    def batch_upload_images(
        self, images: List[UploadedFile], uploaded_by: User
    ) -> List[Dict[str, str]]:
        """
        Batch upload multiple images.

        Args:
            images (List[UploadedFile]): List of images to upload
            folder (str, optional): S3 folder path

        Returns:
            List[Dict[str, str]]: List of upload metadata
        """
        upload_path = generate_upload_path(uploaded_by.uuid)
        return [
            self.upload_image(image, upload_path, uploaded_by)
            for image in images
        ]

    def get_image_url(self, s3_key: str, expiration: int = 3600) -> str:
        """
        Generate a temporary signed URL for private S3 objects.

        Args:
            s3_key (str): S3 object key
            expiration (int, optional): URL expiration time in seconds

        Returns:
            str: Signed URL for image access
        """
        try:
            signed_url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": s3_key},
                ExpiresIn=expiration,
            )
            return signed_url
        except ClientError:
            return None

    def get_image(self, image_uuid):
        return Image.objects.get(uuid=image_uuid)

    def get_images_by_user(self, user_id: str):
        return Image.objects.filter(uploaded_by=user_id)

    def save_image_to_db(
        self,
        image_key: str,
        uploaded_by: User,
    ):
        return Image.objects.create(
            image_key=image_key,
            uploaded_by=uploaded_by,
        )

    def delete_image(image_uuid, user):
        # Ensure that the user owns the image
        image = get_object_or_404(
            Image, uuid=image_uuid, uploaded_by=user.uuid
        )

        # Extract the S3 key from file_url
        file_url = image.image_key
        file_path = f"https://{settings.AWS_CONFIG.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{file_url}"
        delete_image_from_s3(file_path)

        # Delete the image record from the database
        image.delete()
        return True
