"""Connector handlers."""

from __future__ import annotations

from .google_drive import GoogleDriveHandler
from .notion import NotionHandler
from .dropbox import DropboxHandler
from .microsoft import MicrosoftHandler

def get_handler(connector_type: str):
    if connector_type == "google_drive":
        return GoogleDriveHandler
    elif connector_type == "notion":
        return NotionHandler
    elif connector_type == "dropbox":
        return DropboxHandler
    elif connector_type in ["onedrive", "sharepoint"]:
        return MicrosoftHandler
    else:
        return None
