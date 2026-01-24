"""
Helpers for /chat: file uploads -> Converse API image blocks, and ChatMessage -> Converse payload.

- process_uploaded_file: validate size/MIME, return ContentBlock(image={format, source: {bytes}}).
  Raw bytes are required; boto3 base64-encodes for the wire. Pre-encoding to base64 causes errors.
- format_message_for_converse: ChatMessage (str or list of ContentBlocks) -> {role, content: [...]}
  for bedrock_client.converse(messages=...).
"""
import mimetypes

from fastapi import HTTPException, UploadFile

from config import IMAGE_FORMAT_MAP, MAX_FILE_SIZE, SUPPORTED_IMAGE_TYPES
from models import ChatMessage, ContentBlock


def process_uploaded_file(file: UploadFile) -> ContentBlock:
    """
    Validate and convert an uploaded image to a ContentBlock for the Converse API.

    - Size must be <= MAX_FILE_SIZE (3.75 MB). MIME must be in SUPPORTED_IMAGE_TYPES
      (JPEG, PNG, GIF, WebP). Filename required for MIME detection.
    - Returns ContentBlock(image={"format": "jpeg"|"png"|"gif"|"webp", "source": {"bytes": ...}}).
    - Caller should ensure file.file is closed after use.
    """
    file_content = file.file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File '{file.filename}' exceeds maximum size of {MAX_FILE_SIZE / (1024 * 1024):.1f} MB",
        )

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="File must have a filename to determine file type.",
        )

    mime_type, _ = mimetypes.guess_type(file.filename)
    if not mime_type:
        raise HTTPException(
            status_code=400,
            detail=f"Unable to determine file type for '{file.filename}'. Only image files are supported (JPEG, PNG, GIF, WebP).",
        )

    if mime_type not in SUPPORTED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{mime_type}' is not supported. Supported: {', '.join(SUPPORTED_IMAGE_TYPES)}",
        )

    image_format = IMAGE_FORMAT_MAP.get(mime_type, "jpeg")
    return ContentBlock(
        image={"format": image_format, "source": {"bytes": file_content}}
    )


def format_message_for_converse(msg: ChatMessage) -> dict:
    """
    Convert a ChatMessage to the dict shape expected by bedrock_client.converse(messages=...).

    - If content is str: {role, content: [{"text": content}]}.
    - If content is list of ContentBlocks: {role, content: [{"text": ...} | {"image": ...}, ...]}.
    """
    if isinstance(msg.content, str):
        return {"role": msg.role, "content": [{"text": msg.content}]}

    if isinstance(msg.content, list):
        content_blocks = []
        for block in msg.content:
            if block.text:
                content_blocks.append({"text": block.text})
            elif block.image:
                content_blocks.append({"image": block.image})
        return {"role": msg.role, "content": content_blocks}

    raise ValueError(f"Invalid content type for message: {type(msg.content)}")
