"""
This module contains the API endpoints for the uploads service.
"""
from typing import Optional
import uuid

from fastapi import APIRouter, HTTPException, File, UploadFile, Query
from fastapi.responses import JSONResponse
import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.settings import settings, ALLOWED_FILE_EXTENSIONS


router = APIRouter(prefix='/api/v1', tags=['uploads'])

s3 = boto3.client(
    's3',
    endpoint_url=settings.s3_endpoint_url,
    aws_access_key_id=settings.s3_access_key,
    aws_secret_access_key=settings.s3_secret_key,
    region_name=settings.s3_region,
    config=Config(
        signature_version="s3v4",
        s3={'addressing_style': 'path' if settings.s3_endpoint_url.startswith('http') else 'auto'}
        )
)

@router.post("/upload")
def upload(
    file: UploadFile = File(...),
    key: Optional[str] = Query(None),
    upload_id: Optional[str] = Query(None),
    ):
    """
    Start a new upload for a file.

    Args:
        file: The file to upload.

    Returns:
        The response containing the upload information.
    """
    if file.filename is None:
        raise HTTPException(status_code=400, detail="File name is required")
    suffix = file.filename.split('.')[-1]
    if suffix not in ALLOWED_FILE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file extension")
    key = key or f"{uuid.uuid4()}/source.{suffix}"
    upload_id = upload_id or None
    content_type = file.content_type or "application/octet-stream"

    try:
        if upload_id is None:
            resp = s3.create_multipart_upload(
                Bucket=settings.s3_bucket,
                Key=key,
                ContentType=content_type
            )
            upload_id = resp['UploadId']

            parts = []
            part_number = 1
        else:
            parts = [
                {
                    "PartNumber": part["PartNumber"],
                    "ETag": part["ETag"],
                }
                for part in s3.list_parts(
                    Bucket=settings.s3_bucket,
                    Key=key,
                    UploadId=upload_id
                )["Parts"]
            ]
            file.file.seek(len(parts) * settings.part_size_bytes)
            part_number = len(parts) + 1

        while True:
            chunk = file.file.read(settings.part_size_bytes)
            if not chunk:
                break
            part = s3.upload_part(
                Bucket=settings.s3_bucket,
                Key=key,
                UploadId=upload_id,
                PartNumber=part_number,
                Body=chunk
            )
            parts.append(
                {
                    "PartNumber": part_number,
                    "ETag": part["ETag"],
                }
            )
            part_number += 1

        if not parts:
            s3.abort_multipart_upload(
                Bucket=settings.s3_bucket,
                Key=key,
                UploadId=upload_id
            )
            raise HTTPException(status_code=500, detail="No parts uploaded")

        s3.complete_multipart_upload(
            Bucket=settings.s3_bucket,
            Key=key,
            UploadId=upload_id,
            MultipartUpload={'Parts': parts}
        )

    except (ClientError, BotoCoreError) as e:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Upload interrupted; retry with the same file and upload_id",
                "upload_id": upload_id,
                "key": key,
                "parts_uploaded": len(parts),
            },
        ) from e
    finally:
        file.file.close()

    return {
        "upload_id": upload_id,
        "key": key,
        "parts_uploaded": len(parts)
    }

@router.get("/status")
def status(
    key: str,
    upload_id: Optional[str] = Query(None),
    ):
    """
    Get the status of a file upload.
    """
    try:
        parts = s3.list_parts(
            Bucket=settings.s3_bucket,
            Key=key,
            UploadId=upload_id
        )["Parts"]
        return JSONResponse(status_code=200, content={"message": "Upload status", "parts": parts})
    except (ClientError, BotoCoreError) as e:
        raise HTTPException(
            status_code=502,
            detail=f"Upload status: {e}"
        ) from e


@router.delete("/delete_all_parts")
def delete():
    """
    Delete a file from the upload.
    """

    all_parts = s3.list_multipart_uploads(
        Bucket=settings.s3_bucket,
    )['Uploads']

    for part in all_parts:
        s3.abort_multipart_upload(
            Bucket=settings.s3_bucket,
            Key=part['Key'],
            UploadId=part['UploadId']
        )

    return JSONResponse(status_code=200, content={"message": "All uploads deleted"})
