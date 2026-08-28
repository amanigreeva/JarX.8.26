from .service import FileSystemService
from .guard import WorkspaceGuard
from .audit import AuditLogger
from .types import is_text_file

_default_fs_service = None

def get_filesystem_service() -> FileSystemService:
    global _default_fs_service
    if _default_fs_service is None:
        _default_fs_service = FileSystemService()
    return _default_fs_service

__all__ = ["FileSystemService", "WorkspaceGuard", "AuditLogger", "is_text_file", "get_filesystem_service"]
