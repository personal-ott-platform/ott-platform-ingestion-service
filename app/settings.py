"""
This module contains the settings for the uploads service.
"""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict

ALLOWED_FILE_EXTENSIONS = ['mp4', 'mkv']

class Settings(BaseSettings):
    """
    Settings for the uploads service.
    """
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    s3_endpoint_url: str = os.getenv('S3_ENDPOINT_URL')
    s3_access_key: str = os.getenv('S3_ACCESS_KEY')
    s3_secret_key: str = os.getenv('S3_SECRET_KEY')
    s3_region: str = os.getenv('S3_REGION')
    s3_bucket: str = os.getenv('S3_BUCKET')
    part_size_bytes: int = os.getenv('PART_SIZE_BYTES')

settings = Settings()
