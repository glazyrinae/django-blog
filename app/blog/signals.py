"""Signal handlers for blog image management."""

import logging
import os
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Optional
from uuid import uuid4

from django.apps import apps
from django.core.files.base import ContentFile
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from PIL import Image

logger = logging.getLogger("blog")

# Constants
THUMBNAIL_SIZE = (300, 300)
THUMBNAIL_QUALITY = 85
DEFAULT_IMAGE_FORMAT = "JPEG"

FORMAT_MAPPING = {
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".png": "PNG",
    ".webp": "WEBP",
    ".gif": "GIF",
}

# Lazy model loading to avoid circular imports
Images = apps.get_model("blog", "Images")


def generate_unique_filename(original_filename: str) -> str:
    """
    Generate a unique filename with timestamp directory structure.

    Args:
        original_filename: Original file name

    Returns:
        New path with format: YYYY/MM/DD/uuid.ext
    """
    ext = Path(original_filename).suffix.lower()
    new_name = f"{uuid4().hex}{ext}"
    dirname = datetime.now().strftime("%Y/%m/%d")
    result_path = os.path.join(dirname, new_name)
    logger.debug(f"Generated unique filename: {result_path}")
    return result_path


def remove_file_if_exists(file_path: Optional[str]) -> None:
    """
    Safely remove file if it exists.

    Args:
        file_path: Path to the file to remove
    """
    if file_path and os.path.isfile(file_path):
        try:
            os.remove(file_path)
            logger.debug(f"Removed file: {file_path}")
        except OSError as e:
            logger.error(f"Error removing file {file_path}: {e}")


def create_thumbnail(image_file, max_size: tuple = THUMBNAIL_SIZE) -> BytesIO:
    """
    Create a thumbnail from an image file.

    Args:
        image_file: Django ImageField file object
        max_size: Maximum dimensions (width, height)

    Returns:
        BytesIO object containing the thumbnail

    Raises:
        ValueError: If image processing fails
    """
    logger.debug(f"Creating thumbnail for image: {image_file.name}")
    try:
        img = Image.open(image_file)
        original_size = img.size
        logger.debug(f"Original image size: {original_size}")

        # Convert RGBA and P mode images to RGB for JPEG compatibility
        if img.mode in ("RGBA", "P", "LA"):
            logger.debug(f"Converting image from {img.mode} to RGB")
            img = img.convert("RGB")

        # Create thumbnail maintaining aspect ratio
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        logger.debug(f"Thumbnail created with size: {img.size}")

        # Determine image format
        ext = Path(image_file.name).suffix.lower()
        img_format = FORMAT_MAPPING.get(ext, DEFAULT_IMAGE_FORMAT)
        logger.debug(f"Using image format: {img_format}")

        # Save to BytesIO
        thumb_io = BytesIO()
        img.save(thumb_io, format=img_format, quality=THUMBNAIL_QUALITY)
        thumb_io.seek(0)

        logger.info(f"Thumbnail created successfully for {image_file.name}")
        return thumb_io
    except Exception as e:
        logger.error(f"Failed to process image {image_file.name}: {e}", exc_info=True)
        raise ValueError(f"Failed to process image: {str(e)}") from e


def cleanup_old_files(instance, old_instance) -> None:
    """
    Remove old image and thumbnail files when they are replaced.

    Args:
        instance: New model instance
        old_instance: Previous model instance
    """
    logger.debug("Cleaning up old files")

    # Cleanup old main image
    if instance.image and old_instance.image and instance.image != old_instance.image:
        logger.info(f"Removing old image: {old_instance.image.path}")
        remove_file_if_exists(old_instance.image.path)

    # Cleanup old thumbnail
    if (
        instance.thumbnail
        and old_instance.thumbnail
        and instance.thumbnail != old_instance.thumbnail
    ):
        logger.info(f"Removing old thumbnail: {old_instance.thumbnail.path}")
        remove_file_if_exists(old_instance.thumbnail.path)


@receiver(pre_save, sender=Images)
def generate_thumbnail_on_save(sender, instance, **kwargs):
    """
    Generate thumbnail and rename image before saving.

    This signal:
    1. Removes old files when image is replaced
    2. Generates a unique filename for the image
    3. Creates a thumbnail from the uploaded image
    4. Saves both with proper naming

    Args:
        sender: The model class (Images)
        instance: The actual instance being saved
        **kwargs: Additional signal arguments
    """
    logger.info(f"Processing image for post: {instance.post.title}")

    # Handle file updates for existing instances
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            cleanup_old_files(instance, old_instance)
        except sender.DoesNotExist:
            logger.warning(f"Instance with pk={instance.pk} was deleted during processing")

    # Generate thumbnail if image exists
    if not instance.image:
        logger.debug("No image to process, skipping thumbnail generation")
        return

    try:
        # Generate unique filename
        original_name = instance.image.name
        instance.image.name = generate_unique_filename(instance.image.name)
        logger.info(f"Renamed image from {original_name} to {instance.image.name}")

        # Create thumbnail
        thumb_io = create_thumbnail(instance.image, THUMBNAIL_SIZE)

        # Remove old thumbnail if exists
        if instance.thumbnail:
            remove_file_if_exists(instance.thumbnail.path)

        # Save new thumbnail
        thumbnail_name = f"thumb_{Path(instance.image.name).name}"
        instance.thumbnail.save(
            thumbnail_name,
            ContentFile(thumb_io.getvalue()),
            save=False,
        )
        logger.info(f"Thumbnail saved: {thumbnail_name}")

    except Exception as e:
        logger.error(
            f"Image processing error for post '{instance.post.title}': {e}",
            exc_info=True,
        )
        # Clean up instance if thumbnail generation fails
        if instance.pk:
            logger.warning("Deleting instance due to image processing failure")
            instance.delete()
        raise ValueError(f"Image processing error: {str(e)}") from e


@receiver(post_delete, sender=Images)
def cleanup_files_on_delete(sender, instance, **kwargs):
    """
    Remove image and thumbnail files when model instance is deleted.

    Args:
        sender: The model class (Images)
        instance: The instance being deleted
        **kwargs: Additional signal arguments
    """
    if sender == Images:
        logger.info(f"Cleaning up files for deleted image (ID: {instance.pk})")
        remove_file_if_exists(instance.image.path)
        remove_file_if_exists(instance.thumbnail.path)
        logger.debug("File cleanup completed")
