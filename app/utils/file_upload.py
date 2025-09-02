import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException
import logging
from typing import Optional
import uuid
import mimetypes

from app.config import settings

logger = logging.getLogger(__name__)


class FileUploadService:
    """Handle file uploads to Cloudflare R2"""
    
    def __init__(self):
        self.s3_client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize S3-compatible client for Cloudflare R2"""
        if not all([
            settings.r2_access_key_id,
            settings.r2_secret_access_key,
            settings.r2_endpoint_url,
            settings.r2_bucket_name
        ]):
            logger.warning("R2 credentials not configured")
            return
        
        try:
            self.s3_client = boto3.client(
                's3',
                endpoint_url=settings.r2_endpoint_url,
                aws_access_key_id=settings.r2_access_key_id,
                aws_secret_access_key=settings.r2_secret_access_key,
                region_name='auto'  # Cloudflare R2 uses 'auto'
            )
            logger.info("R2 client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize R2 client: {e}")
    
    async def upload_file(
        self, 
        file_content: bytes, 
        filename: str, 
        content_type: Optional[str] = None,
        folder: str = "uploads"
    ) -> str:
        """Upload file to R2 and return public URL"""
        
        if not self.s3_client:
            raise HTTPException(
                status_code=500,
                detail="File upload service not available"
            )
        
        try:
            # Generate unique filename
            file_extension = filename.split('.')[-1] if '.' in filename else ''
            unique_filename = f"{uuid.uuid4()}.{file_extension}" if file_extension else str(uuid.uuid4())
            
            # Object key (path in bucket)
            object_key = f"{folder}/{unique_filename}"
            
            # Determine content type
            if not content_type:
                content_type, _ = mimetypes.guess_type(filename)
                if not content_type:
                    content_type = 'application/octet-stream'
            
            # Upload file
            self.s3_client.put_object(
                Bucket=settings.r2_bucket_name,
                Key=object_key,
                Body=file_content,
                ContentType=content_type,
                # Make file publicly readable
                ACL='public-read'
            )
            
            # Generate public URL
            public_url = f"{settings.r2_endpoint_url}/{settings.r2_bucket_name}/{object_key}"
            
            logger.info(f"File uploaded successfully: {object_key}")
            return public_url
            
        except ClientError as e:
            logger.error(f"Failed to upload file: {e}")
            raise HTTPException(
                status_code=500,
                detail="File upload failed"
            )
        except Exception as e:
            logger.error(f"Unexpected error during file upload: {e}")
            raise HTTPException(
                status_code=500,
                detail="File upload failed"
            )
    
    async def delete_file(self, file_url: str) -> bool:
        """Delete file from R2"""
        
        if not self.s3_client:
            logger.warning("R2 client not available for file deletion")
            return False
        
        try:
            # Extract object key from URL
            # Expected format: https://endpoint/bucket/folder/filename
            url_parts = file_url.split('/')
            if len(url_parts) < 2:
                logger.error("Invalid file URL format")
                return False
            
            object_key = '/'.join(url_parts[-2:])  # folder/filename
            
            # Delete object
            self.s3_client.delete_object(
                Bucket=settings.r2_bucket_name,
                Key=object_key
            )
            
            logger.info(f"File deleted successfully: {object_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            return False


# Global file upload service instance
file_service = FileUploadService()
