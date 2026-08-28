import os
import shutil
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

from .guard import WorkspaceGuard
from .types import is_text_file
from .audit import AuditLogger

class FileSystemService:
    """
    Core FileSystem service implementing controlled and safe CRUD operations
    on the user's Windows filesystem.
    """

    def __init__(self, guard: Optional[WorkspaceGuard] = None, audit: Optional[AuditLogger] = None):
        self.guard = guard or WorkspaceGuard()
        self.audit = audit or AuditLogger()
        self.max_file_size = int(os.getenv("JARX_MAX_FILE_SIZE", str(5 * 1024 * 1024))) # 5MB default

    def list_directory(self, path: Optional[str] = None) -> Dict[str, Any]:
        target_path = path or str(self.guard.get_default_workspace())
        try:
            resolved = self.guard.validate_and_resolve(target_path)
            if not resolved.exists():
                raise FileNotFoundError(f"Directory not found: '{resolved}'")
            if not resolved.is_dir():
                raise NotADirectoryError(f"Path is not a directory: '{resolved}'")

            items = []
            for item in sorted(resolved.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                try:
                    stat = item.stat()
                    items.append({
                        "name": item.name,
                        "path": str(item),
                        "is_dir": item.is_dir(),
                        "size": stat.st_size if not item.is_dir() else None,
                        "modified": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)),
                    })
                except Exception:
                    continue

            self.audit.log("list_directory", str(resolved), True, f"Listed {len(items)} items")
            return {
                "success": True,
                "operation": "list_directory",
                "path": str(resolved),
                "items": items,
                "count": len(items)
            }
        except Exception as e:
            self.audit.log("list_directory", str(target_path), False, str(e))
            return {"success": False, "operation": "list_directory", "error": str(e)}

    def read_file(self, path: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> Dict[str, Any]:
        try:
            resolved = self.guard.validate_and_resolve(path)
            if not resolved.exists():
                raise FileNotFoundError(f"File not found: '{resolved}'")
            if resolved.is_dir():
                raise IsADirectoryError(f"Path is a directory, not a file: '{resolved}'")

            file_size = resolved.stat().st_size
            if not is_text_file(resolved):
                self.audit.log("read_file", str(resolved), True, "Binary file inspection")
                return {
                    "success": True,
                    "operation": "read_file",
                    "path": str(resolved),
                    "is_binary": True,
                    "size": file_size,
                    "message": f"Binary file detected ({resolved.suffix}). Content not displayed directly."
                }

            if file_size > self.max_file_size and (start_line is None and end_line is None):
                # Read first 100 lines
                with open(resolved, "r", encoding="utf-8", errors="replace") as f:
                    lines = [f.readline() for _ in range(100)]
                content = "".join(lines)
                truncated = True
            else:
                with open(resolved, "r", encoding="utf-8", errors="replace") as f:
                    all_lines = f.readlines()
                
                if start_line is not None or end_line is not None:
                    s = max(0, (start_line or 1) - 1)
                    e = min(len(all_lines), end_line or len(all_lines))
                    content = "".join(all_lines[s:e])
                    truncated = (e - s) < len(all_lines)
                else:
                    content = "".join(all_lines)
                    truncated = False

            self.audit.log("read_file", str(resolved), True, f"Read {len(content)} chars")
            return {
                "success": True,
                "operation": "read_file",
                "path": str(resolved),
                "content": content,
                "size": file_size,
                "truncated": truncated
            }
        except Exception as e:
            self.audit.log("read_file", str(path), False, str(e))
            return {"success": False, "operation": "read_file", "error": str(e)}

    def create_file(self, path: str, content: str = "", overwrite: bool = False) -> Dict[str, Any]:
        try:
            resolved = self.guard.validate_and_resolve(path)
            if resolved.exists() and not overwrite:
                raise FileExistsError(f"File already exists: '{resolved}'. Set overwrite=True to replace.")
            
            resolved.parent.mkdir(parents=True, exist_ok=True)
            with open(resolved, "w", encoding="utf-8") as f:
                f.write(content)

            self.audit.log("create_file", str(resolved), True, f"Wrote {len(content)} bytes")
            return {
                "success": True,
                "operation": "create_file",
                "path": str(resolved),
                "size": len(content),
                "message": f"Successfully created file '{resolved.name}'."
            }
        except Exception as e:
            self.audit.log("create_file", str(path), False, str(e))
            return {"success": False, "operation": "create_file", "error": str(e)}

    def create_directory(self, path: str) -> Dict[str, Any]:
        try:
            resolved = self.guard.validate_and_resolve(path)
            resolved.mkdir(parents=True, exist_ok=True)
            self.audit.log("create_directory", str(resolved), True)
            return {
                "success": True,
                "operation": "create_directory",
                "path": str(resolved),
                "message": f"Successfully created directory '{resolved}'."
            }
        except Exception as e:
            self.audit.log("create_directory", str(path), False, str(e))
            return {"success": False, "operation": "create_directory", "error": str(e)}

    def update_file(self, path: str, content: str, mode: str = "overwrite") -> Dict[str, Any]:
        """
        mode: 'overwrite' or 'append'
        """
        try:
            resolved = self.guard.validate_and_resolve(path)
            if not resolved.exists():
                raise FileNotFoundError(f"File not found: '{resolved}'")
            if resolved.is_dir():
                raise IsADirectoryError(f"Path is a directory: '{resolved}'")

            write_mode = "a" if mode.lower() == "append" else "w"
            with open(resolved, write_mode, encoding="utf-8") as f:
                f.write(content)

            self.audit.log("update_file", str(resolved), True, f"Mode={mode}, bytes={len(content)}")
            return {
                "success": True,
                "operation": "update_file",
                "path": str(resolved),
                "mode": mode,
                "size": resolved.stat().st_size,
                "message": f"Successfully updated '{resolved.name}' ({mode})."
            }
        except Exception as e:
            self.audit.log("update_file", str(path), False, str(e))
            return {"success": False, "operation": "update_file", "error": str(e)}

    def delete_file(self, path: str, confirmed: bool = False) -> Dict[str, Any]:
        try:
            resolved = self.guard.validate_and_resolve(path)
            if not resolved.exists():
                raise FileNotFoundError(f"File not found: '{resolved}'")
            if resolved.is_dir():
                raise IsADirectoryError(f"Target is a directory, use delete_directory: '{resolved}'")

            req_conf = os.getenv("JARX_REQUIRE_DELETE_CONFIRMATION", "true").lower() in ("true", "1", "yes")
            if req_conf and not confirmed:
                return {
                    "success": False,
                    "operation": "delete_file",
                    "confirmation_required": True,
                    "path": str(resolved),
                    "message": f"Confirmation required to delete '{resolved}'. Please confirm deletion."
                }

            resolved.unlink()
            self.audit.log("delete_file", str(resolved), True)
            return {
                "success": True,
                "operation": "delete_file",
                "path": str(resolved),
                "message": f"Deleted file '{resolved.name}'."
            }
        except Exception as e:
            self.audit.log("delete_file", str(path), False, str(e))
            return {"success": False, "operation": "delete_file", "error": str(e)}

    def delete_directory(self, path: str, recursive: bool = False, confirmed: bool = False) -> Dict[str, Any]:
        try:
            resolved = self.guard.validate_and_resolve(path)
            if not resolved.exists():
                raise FileNotFoundError(f"Directory not found: '{resolved}'")
            if not resolved.is_dir():
                raise NotADirectoryError(f"Target is not a directory: '{resolved}'")

            req_conf = os.getenv("JARX_REQUIRE_DELETE_CONFIRMATION", "true").lower() in ("true", "1", "yes")
            if req_conf and not confirmed:
                return {
                    "success": False,
                    "operation": "delete_directory",
                    "confirmation_required": True,
                    "path": str(resolved),
                    "message": f"Confirmation required to delete directory '{resolved}'."
                }

            if recursive:
                shutil.rmtree(resolved)
            else:
                resolved.rmdir()

            self.audit.log("delete_directory", str(resolved), True, f"recursive={recursive}")
            return {
                "success": True,
                "operation": "delete_directory",
                "path": str(resolved),
                "message": f"Deleted directory '{resolved}'."
            }
        except Exception as e:
            self.audit.log("delete_directory", str(path), False, str(e))
            return {"success": False, "operation": "delete_directory", "error": str(e)}

    def rename_file(self, src: str, new_name: str) -> Dict[str, Any]:
        try:
            src_resolved = self.guard.validate_and_resolve(src)
            if not src_resolved.exists():
                raise FileNotFoundError(f"Source not found: '{src_resolved}'")
            
            # Destination in same directory
            dest_resolved = src_resolved.parent / new_name
            dest_resolved = self.guard.validate_and_resolve(dest_resolved)
            if dest_resolved.exists():
                raise FileExistsError(f"Destination already exists: '{dest_resolved}'")

            src_resolved.rename(dest_resolved)
            self.audit.log("rename_file", f"{src_resolved} -> {dest_resolved}", True)
            return {
                "success": True,
                "operation": "rename_file",
                "old_path": str(src_resolved),
                "new_path": str(dest_resolved),
                "message": f"Renamed to '{dest_resolved.name}'."
            }
        except Exception as e:
            self.audit.log("rename_file", str(src), False, str(e))
            return {"success": False, "operation": "rename_file", "error": str(e)}

    def move_file(self, src: str, dest: str, confirmed: bool = False) -> Dict[str, Any]:
        try:
            src_resolved = self.guard.validate_and_resolve(src)
            dest_resolved = self.guard.validate_and_resolve(dest)
            if not src_resolved.exists():
                raise FileNotFoundError(f"Source not found: '{src_resolved}'")

            if dest_resolved.is_dir():
                dest_resolved = dest_resolved / src_resolved.name

            req_conf = os.getenv("JARX_REQUIRE_DELETE_CONFIRMATION", "true").lower() in ("true", "1", "yes")
            if req_conf and not confirmed:
                return {
                    "success": False,
                    "operation": "move_file",
                    "confirmation_required": True,
                    "src": str(src_resolved),
                    "dest": str(dest_resolved),
                    "message": f"Confirmation required to move '{src_resolved}' to '{dest_resolved}'."
                }

            shutil.move(str(src_resolved), str(dest_resolved))
            self.audit.log("move_file", f"{src_resolved} -> {dest_resolved}", True)
            return {
                "success": True,
                "operation": "move_file",
                "src": str(src_resolved),
                "dest": str(dest_resolved),
                "message": f"Moved '{src_resolved.name}' to '{dest_resolved}'."
            }
        except Exception as e:
            self.audit.log("move_file", str(src), False, str(e))
            return {"success": False, "operation": "move_file", "error": str(e)}

    def copy_file(self, src: str, dest: str) -> Dict[str, Any]:
        try:
            src_resolved = self.guard.validate_and_resolve(src)
            dest_resolved = self.guard.validate_and_resolve(dest)
            if not src_resolved.exists():
                raise FileNotFoundError(f"Source not found: '{src_resolved}'")

            if dest_resolved.is_dir():
                dest_resolved = dest_resolved / src_resolved.name

            if src_resolved.is_dir():
                shutil.copytree(src_resolved, dest_resolved)
            else:
                shutil.copy2(src_resolved, dest_resolved)

            self.audit.log("copy_file", f"{src_resolved} -> {dest_resolved}", True)
            return {
                "success": True,
                "operation": "copy_file",
                "src": str(src_resolved),
                "dest": str(dest_resolved),
                "message": f"Copied '{src_resolved.name}' to '{dest_resolved}'."
            }
        except Exception as e:
            self.audit.log("copy_file", str(src), False, str(e))
            return {"success": False, "operation": "copy_file", "error": str(e)}

    def file_exists(self, path: str) -> Dict[str, Any]:
        try:
            resolved = self.guard.validate_and_resolve(path)
            exists = resolved.exists()
            return {
                "success": True,
                "operation": "file_exists",
                "path": str(resolved),
                "exists": exists,
                "is_dir": resolved.is_dir() if exists else False
            }
        except Exception as e:
            return {"success": False, "operation": "file_exists", "error": str(e)}

    def get_file_info(self, path: str) -> Dict[str, Any]:
        try:
            resolved = self.guard.validate_and_resolve(path)
            if not resolved.exists():
                raise FileNotFoundError(f"Path not found: '{resolved}'")

            stat = resolved.stat()
            is_dir = resolved.is_dir()
            return {
                "success": True,
                "operation": "get_file_info",
                "name": resolved.name,
                "path": str(resolved),
                "is_dir": is_dir,
                "is_text": is_text_file(resolved) if not is_dir else False,
                "size": stat.st_size if not is_dir else None,
                "created": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_ctime)),
                "modified": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)),
            }
        except Exception as e:
            return {"success": False, "operation": "get_file_info", "error": str(e)}
