"""
Database data models for Dissound.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Sound:
    sound_id: str
    sound_name: str
    category: str
    file_path: str
    duration: float
    file_size: int
    file_format: str
    source_url: str = ""
    tags: str = ""
    created_at: Optional[datetime] = None

@dataclass
class Server:
    server_id: str
    server_name: str
    sound_limit: int = 8
    created_at: Optional[datetime] = None

@dataclass
class User:
    user_id: str
    username: str
    permissions: str = "member"

@dataclass
class UploadHistoryItem:
    upload_id: Optional[int]
    server_id: str
    user_id: str
    sound_id: str
    sound_name: str
    upload_status: str
    error_message: Optional[str] = None
    timestamp: Optional[datetime] = None
