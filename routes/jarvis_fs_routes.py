from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from services.filesystem import get_filesystem_service

router = APIRouter(prefix="/api/filesystem", tags=["filesystem"])

class ListReq(BaseModel):
    path: Optional[str] = None

class ReadReq(BaseModel):
    path: str
    start_line: Optional[int] = None
    end_line: Optional[int] = None

class CreateFileReq(BaseModel):
    path: str
    content: str = ""
    overwrite: bool = False

class CreateDirReq(BaseModel):
    path: str

class UpdateFileReq(BaseModel):
    path: str
    content: str
    mode: str = "overwrite"

class DeleteReq(BaseModel):
    path: str
    recursive: bool = False
    confirmed: bool = False

class RenameReq(BaseModel):
    src: str
    new_name: str

class MoveReq(BaseModel):
    src: str
    dest: str
    confirmed: bool = False

class CopyReq(BaseModel):
    src: str
    dest: str

@router.get("/status")
async def get_status():
    fs = get_filesystem_service()
    return {
        "status": "active",
        "default_workspace": str(fs.guard.get_default_workspace()),
        "allowed_roots": [str(r) for r in fs.guard.allowed_roots],
        "max_file_size": fs.max_file_size
    }

@router.post("/list")
async def list_dir(req: ListReq):
    fs = get_filesystem_service()
    res = fs.list_directory(req.path)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res

@router.post("/read")
async def read_f(req: ReadReq):
    fs = get_filesystem_service()
    res = fs.read_file(req.path, req.start_line, req.end_line)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res

@router.post("/create-file")
async def create_f(req: CreateFileReq):
    fs = get_filesystem_service()
    res = fs.create_file(req.path, req.content, req.overwrite)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res

@router.post("/create-dir")
async def create_d(req: CreateDirReq):
    fs = get_filesystem_service()
    res = fs.create_directory(req.path)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res

@router.post("/update-file")
async def update_f(req: UpdateFileReq):
    fs = get_filesystem_service()
    res = fs.update_file(req.path, req.content, req.mode)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res

@router.post("/delete")
async def delete_item(req: DeleteReq):
    fs = get_filesystem_service()
    res = fs.delete_file(req.path, req.confirmed)
    if not res.get("success") and not res.get("confirmation_required"):
        # try as directory
        res = fs.delete_directory(req.path, req.recursive, req.confirmed)
    if not res.get("success") and not res.get("confirmation_required"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res

@router.post("/rename")
async def rename_item(req: RenameReq):
    fs = get_filesystem_service()
    res = fs.rename_file(req.src, req.new_name)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res

@router.post("/move")
async def move_item(req: MoveReq):
    fs = get_filesystem_service()
    res = fs.move_file(req.src, req.dest, req.confirmed)
    if not res.get("success") and not res.get("confirmation_required"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res

@router.post("/copy")
async def copy_item(req: CopyReq):
    fs = get_filesystem_service()
    res = fs.copy_file(req.src, req.dest)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res
