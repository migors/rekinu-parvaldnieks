"""Google Drive upload utility using OAuth2 user credentials."""

import json
import logging
from io import BytesIO
from typing import Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def _get_credentials(settings: dict) -> Optional[Credentials]:
    """Build OAuth2 credentials from stored settings."""
    client_id = settings.get("gdrive_client_id", "").strip()
    client_secret = settings.get("gdrive_client_secret", "").strip()
    refresh_token = settings.get("gdrive_refresh_token", "").strip()

    if not client_id or not client_secret or not refresh_token:
        return None

    return Credentials(
        token=None,
        refresh_token=refresh_token,
        client_id=client_id,
        client_secret=client_secret,
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )


def _get_drive_service(settings: dict):
    """Create a Google Drive API service from OAuth2 credentials."""
    creds = _get_credentials(settings)
    if not creds:
        return None
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def get_auth_url(client_id: str, client_secret: str, redirect_uri: str) -> str:
    """Generate Google OAuth2 authorization URL."""
    from google_auth_oauthlib.flow import Flow

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=redirect_uri,
    )
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",
    )
    return auth_url


def exchange_code(code: str, client_id: str, client_secret: str, redirect_uri: str) -> str:
    """Exchange authorization code for a refresh token."""
    from google_auth_oauthlib.flow import Flow

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=redirect_uri,
    )
    flow.fetch_token(code=code)
    return flow.credentials.refresh_token


def upload_to_gdrive(
    pdf_bytes: bytes,
    filename: str,
    settings: dict,
) -> Optional[str]:
    """Upload a PDF file to Google Drive.

    Returns the file ID on success, or None on failure.
    """
    enabled = settings.get("gdrive_enabled", "false")
    folder_id = settings.get("gdrive_folder_id", "").strip()

    if enabled != "true" or not folder_id:
        return None

    try:
        service = _get_drive_service(settings)
        if not service:
            logger.error("Google Drive: missing OAuth2 credentials")
            return None

        file_metadata = {
            "name": filename,
            "parents": [folder_id],
        }

        media = MediaIoBaseUpload(
            BytesIO(pdf_bytes),
            mimetype="application/pdf",
            resumable=False,
        )

        file = (
            service.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )

        file_id = file.get("id")
        logger.info(f"PDF uploaded to Google Drive: {filename} (id={file_id})")
        return file_id

    except Exception as e:
        logger.error(f"Google Drive upload failed for {filename}: {e}")
        return None
