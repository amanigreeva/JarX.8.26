import os
from pathlib import Path
from typing import List, Union

class WorkspaceGuard:
    """
    Validates filesystem paths against configured allowed roots to prevent
    directory traversal attacks, symlink escape, and unauthorized system access.
    """

    def __init__(self, workspace_root: Union[str, Path, None] = None, extra_roots: List[str] = None):
        roots = []
        if workspace_root:
            roots.append(Path(workspace_root).expanduser().resolve())
        else:
            env_ws = os.getenv("JARX_WORKSPACE")
            if env_ws:
                roots.append(Path(env_ws).expanduser().resolve())
            else:
                user_home = Path.home()
                roots.append((user_home / "Downloads").resolve())
                roots.append((user_home / "Desktop").resolve())
                roots.append((user_home / "Documents").resolve())

        env_extra = os.getenv("JARX_EXTRA_ALLOWED_PATHS", "")
        if env_extra:
            for p in env_extra.split(","):
                if p.strip():
                    roots.append(Path(p.strip()).expanduser().resolve())

        if extra_roots:
            for p in extra_roots:
                if p:
                    roots.append(Path(p).expanduser().resolve())

        self.allowed_roots = list(dict.fromkeys(roots))

    def get_default_workspace(self) -> Path:
        return self.allowed_roots[0] if self.allowed_roots else Path.home() / "Downloads"

    def is_allowed(self, path: Union[str, Path]) -> bool:
        try:
            target = Path(path).expanduser().resolve()
            for root in self.allowed_roots:
                if target == root or root in target.parents:
                    return True
            return False
        except Exception:
            return False

    def validate_and_resolve(self, path: Union[str, Path]) -> Path:
        if not path or not str(path).strip():
            raise ValueError("Path cannot be empty.")

        target = Path(path).expanduser().resolve()
        if not self.is_allowed(target):
            roots_str = ", ".join(str(r) for r in self.allowed_roots)
            raise PermissionError(
                f"Access denied: '{target}' is outside the allowed workspace directories [{roots_str}]."
            )
        return target
