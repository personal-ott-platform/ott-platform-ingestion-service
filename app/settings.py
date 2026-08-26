from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    s3_endpoint_url: str
    s3_access_key: str
    s3_secret_key: str
    s3_region: str
    s3_bucket: str
    part_size_bytes: int = 8 * 1024 * 1024

settings = Settings()
