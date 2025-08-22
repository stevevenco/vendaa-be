import uuid
from typing import Dict, List

import cloudinary
import cloudinary.uploader
import cloudinary.utils
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.shortcuts import get_object_or_404

from authentication.models import User
from media.features.image.models import Image, generate_upload_path


class ImageService:
    """
    Service class for handling image uploads,
    validations, and retrievals using Cloudinary.
    Follows SOLID principles with single
    responsibility and dependency inversion.
    """

    def __init__(self):
        """
        Initialize Cloudinary configuration from Django settings.
        """
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CONFIG.CLOUD_NAME,
            api_key=settings.CLOUDINARY_CONFIG.API_KEY,
            api_secret=settings.CLOUDINARY_CONFIG.API_SECRET,
            secure=True,
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
        valid_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
        return image.content_type in valid_types

    def generate_unique_filename(self, original_filename: str) -> str:
        """
        Generate a unique filename with UUID and original extension.

        Args:
            original_filename (str): Original uploaded filename

        Returns:
            str: Unique filename
        """
        extension = original_filename.split(".")[-1].lower()
        return f"{uuid.uuid4()}.{extension}"

    def upload_image(
        self,
        image: UploadedFile,
        folder: str,
        uploaded_by: User,
        collection_id: str,
    ) -> Dict[str, str]:
        """
        Upload single image to Cloudinary with validation and unique naming.

        Args:
            image (UploadedFile): Image file to upload
            folder (str): Cloudinary folder path
            uploaded_by (User): User who uploaded the image
            collection_id (str): Collection ID for the image

        Returns:
            Dict[str, str]: Upload metadata
        """
        if not self.validate_image(image):
            raise ValueError("Invalid image file")

        unique_filename = self.generate_unique_filename(image.name)

        try:
            # Upload to Cloudinary
            # upload_result = cloudinary.uploader.upload(
            #     image,
            #     public_id=f"{folder}/{unique_filename}",
            #     resource_type="image",
            #     folder=folder,
            #     access_mode="authenticated"  # Private by default
            # )

            upload_result = cloudinary.uploader.upload(
                image,
                public_id=f"{folder}/{unique_filename}",
                resource_type="image",
                folder=folder,
                access_mode="public",  # Explicitly set to public
            )

            # Save image details to database
            self.save_image_to_db(
                image_key=upload_result["public_id"],
                collection_id=collection_id,
                uploaded_by=uploaded_by,
            )

            return {
                "url": upload_result["secure_url"],
                "key": upload_result["public_id"],
            }

        except Exception as e:
            raise RuntimeError(f"Cloudinary Upload Error: {str(e)}")

    def batch_upload_images(
        self, collection_id: str, images: List[UploadedFile], uploaded_by: User
    ) -> List[Dict[str, str]]:
        """
        Batch upload multiple images.

        Args:
            collection_id (str): Collection ID for the images
            images (List[UploadedFile]): List of images to upload
            uploaded_by (User): User who uploaded the images

        Returns:
            List[Dict[str, str]]: List of upload metadata
        """
        upload_path = generate_upload_path(collection_id)
        return [
            self.upload_image(image, upload_path, uploaded_by, collection_id)
            for image in images
        ]

    def get_image_url(self, public_id: str, expiration: int = 3600) -> str:
        """
        Generate a temporary signed URL for private Cloudinary images.

        Args:
            public_id (str): Cloudinary public ID
            expiration (int, optional): URL expiration time in seconds

        Returns:
            str: Signed URL for image access
        """
        try:
            # return cloudinary.utils.cloudinary_url(
            #     public_id,
            #     secure=True,
            #     sign_url=True,
            #     type="authenticated",
            #     expires_at=int(expiration)
            # )[0]

            # Generate URL for public images
            return cloudinary.utils.cloudinary_url(
                public_id,
                secure=True,
                sign_url=False,  # Public images don't require signing
                type="upload",  # Default type for public images
            )[0]
        except Exception:
            return None

    def get_image(self, image_uuid):
        """Get image by UUID."""
        return Image.objects.get(uuid=image_uuid)

    def get_images_by_collection(self, collection_id: str):
        """Get all images in a collection."""
        return Image.objects.filter(collection_id=collection_id)

    def save_image_to_db(
        self,
        image_key: str,
        collection_id: str,
        uploaded_by: User,
    ):
        """Save image metadata to database."""
        return Image.objects.create(
            image_key=image_key,
            collection_id=collection_id,
            uploaded_by=uploaded_by,
        )

    def delete_image(self, image_uuid: str, user: User) -> bool:
        """
        Delete image from Cloudinary and database.

        Args:
            image_uuid (str): Image UUID
            user (User): User requesting deletion

        Returns:
            bool: Whether deletion was successful
        """
        # Ensure that the user owns the image
        image = get_object_or_404(
            Image, uuid=image_uuid, uploaded_by=user.hiver.uuid
        )

        try:
            # Delete from Cloudinary
            cloudinary.uploader.destroy(image.image_key)

            # Delete the image record from the database
            image.delete()
            return True
        except Exception as e:
            raise RuntimeError(f"Cloudinary Deletion Error: {str(e)}")
