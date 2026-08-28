import os
import shutil
import tempfile
import pytest
from pathlib import Path

from services.filesystem.guard import WorkspaceGuard
from services.filesystem.service import FileSystemService
from services.filesystem.types import is_text_file

@pytest.fixture
def temp_workspace():
    temp_dir = tempfile.mkdtemp(prefix="jarx_test_ws_")
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)

def test_guard_allowed_paths(temp_workspace):
    guard = WorkspaceGuard(workspace_root=temp_workspace)
    assert guard.is_allowed(temp_workspace / "test.txt")
    assert guard.is_allowed(temp_workspace / "sub" / "folder" / "file.py")
    
    # Path traversal attempts
    assert not guard.is_allowed(temp_workspace / ".." / "outside.txt")
    assert not guard.is_allowed(Path("C:/Windows/System32"))

def test_file_crud_operations(temp_workspace):
    guard = WorkspaceGuard(workspace_root=temp_workspace)
    fs = FileSystemService(guard=guard)
    
    test_file = temp_workspace / "hello.txt"
    
    # 1. Create file
    res = fs.create_file(str(test_file), "Hello World", overwrite=False)
    assert res["success"] is True
    assert test_file.exists()
    assert test_file.read_text(encoding="utf-8") == "Hello World"
    
    # Duplicate creation without overwrite fails
    res_dup = fs.create_file(str(test_file), "Duplicate", overwrite=False)
    assert res_dup["success"] is False
    
    # 2. Read file
    res_read = fs.read_file(str(test_file))
    assert res_read["success"] is True
    assert res_read["content"] == "Hello World"
    
    # 3. Update file (overwrite & append)
    res_update = fs.update_file(str(test_file), " Appended", mode="append")
    assert res_update["success"] is True
    assert test_file.read_text(encoding="utf-8") == "Hello World Appended"
    
    # 4. File Info & Exists
    res_info = fs.get_file_info(str(test_file))
    assert res_info["success"] is True
    assert res_info["is_text"] is True
    assert res_info["size"] > 0
    
    res_exists = fs.file_exists(str(test_file))
    assert res_exists["success"] is True
    assert res_exists["exists"] is True
    
    # 5. Rename
    res_rename = fs.rename_file(str(test_file), "renamed.txt")
    assert res_rename["success"] is True
    assert not test_file.exists()
    assert (temp_workspace / "renamed.txt").exists()
    
    # 6. Delete file (confirmation test)
    renamed_file = temp_workspace / "renamed.txt"
    res_del_no_conf = fs.delete_file(str(renamed_file), confirmed=False)
    assert res_del_no_conf["confirmation_required"] is True
    assert renamed_file.exists()
    
    res_del_conf = fs.delete_file(str(renamed_file), confirmed=True)
    assert res_del_conf["success"] is True
    assert not renamed_file.exists()

def test_directory_operations(temp_workspace):
    guard = WorkspaceGuard(workspace_root=temp_workspace)
    fs = FileSystemService(guard=guard)
    
    folder = temp_workspace / "test_folder"
    res_dir = fs.create_directory(str(folder))
    assert res_dir["success"] is True
    assert folder.is_dir()
    
    # Create file inside
    f = folder / "item.txt"
    fs.create_file(str(f), "data")
    
    # List directory
    res_list = fs.list_directory(str(folder))
    assert res_list["success"] is True
    assert res_list["count"] == 1
    assert res_list["items"][0]["name"] == "item.txt"
    
    # Delete directory recursively
    res_del = fs.delete_directory(str(folder), recursive=True, confirmed=True)
    assert res_del["success"] is True
    assert not folder.exists()
