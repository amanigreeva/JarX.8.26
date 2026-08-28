from pathlib import Path
from typing import Tuple

TEXT_EXTENSIONS = {
    ".txt", ".md", ".json", ".xml", ".csv", ".py", ".js", ".ts", ".jsx", ".tsx",
    ".java", ".cpp", ".c", ".h", ".hpp", ".cs", ".go", ".rs", ".rb", ".php",
    ".html", ".css", ".scss", ".sass", ".yaml", ".yml", ".env", ".toml", ".ini",
    ".cfg", ".conf", ".sh", ".bat", ".ps1", ".log", ".sql", ".rst", ".tsv"
}

BINARY_EXTENSIONS = {
    ".exe", ".dll", ".so", ".dylib", ".zip", ".tar", ".gz", ".7z", ".rar",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".ico", ".svg",
    ".mp3", ".wav", ".ogg", ".flac", ".mp4", ".mov", ".avi", ".mkv",
    ".bin", ".dat", ".db", ".sqlite", ".iso", ".img"
}

def is_text_file(path: Path) -> bool:
    ext = path.suffix.lower()
    if ext in TEXT_EXTENSIONS:
        return True
    if ext in BINARY_EXTENSIONS:
        return False
    
    # Heuristic for files without clear extension
    if path.exists() and path.is_file():
        try:
            with open(path, "rb") as f:
                chunk = f.read(1024)
                if b"\x00" in chunk:
                    return False
                chunk.decode("utf-8")
                return True
        except UnicodeDecodeError:
            return False
        except Exception:
            return False
    return True
