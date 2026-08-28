import json
from typing import Dict, Any
from services.filesystem import get_filesystem_service

def _parse_tool_args(content: str) -> Dict[str, Any]:
    text = str(content or "").strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except Exception:
        # Fallback: single string argument as path
        return {"path": text}

class ListDirectoryTool:
    async def execute(self, content: str, ctx: dict) -> dict:
        args = _parse_tool_args(content)
        path = args.get("path")
        fs = get_filesystem_service()
        res = fs.list_directory(path)
        if res.get("success"):
            items_str = "\n".join([f"- {'[DIR] ' if i['is_dir'] else '[FILE]'} {i['name']} ({i['size']} bytes)" if not i['is_dir'] else f"- [DIR]  {i['name']}" for i in res.get("items", [])])
            out = f"Directory contents of {res.get('path')} ({res.get('count')} items):\n{items_str}" if items_str else f"Directory {res.get('path')} is empty."
            return {"output": out, "exit_code": 0, "result": res}
        return {"output": f"Error: {res.get('error')}", "exit_code": 1, "result": res}

class ReadFileFsTool:
    async def execute(self, content: str, ctx: dict) -> dict:
        args = _parse_tool_args(content)
        path = args.get("path")
        s = args.get("start_line")
        e = args.get("end_line")
        fs = get_filesystem_service()
        res = fs.read_file(path, s, e)
        if res.get("success"):
            if res.get("is_binary"):
                return {"output": res.get("message"), "exit_code": 0, "result": res}
            trunc = " (Truncated)" if res.get("truncated") else ""
            out = f"File: {res.get('path')}{trunc}\n---\n{res.get('content')}"
            return {"output": out, "exit_code": 0, "result": res}
        return {"output": f"Error: {res.get('error')}", "exit_code": 1, "result": res}

class CreateFileFsTool:
    async def execute(self, content: str, ctx: dict) -> dict:
        args = _parse_tool_args(content)
        path = args.get("path")
        body = args.get("content", "")
        overwrite = args.get("overwrite", False)
        fs = get_filesystem_service()
        res = fs.create_file(path, body, overwrite)
        if res.get("success"):
            return {"output": res.get("message"), "exit_code": 0, "result": res}
        return {"output": f"Error: {res.get('error')}", "exit_code": 1, "result": res}

class CreateDirectoryFsTool:
    async def execute(self, content: str, ctx: dict) -> dict:
        args = _parse_tool_args(content)
        path = args.get("path")
        fs = get_filesystem_service()
        res = fs.create_directory(path)
        if res.get("success"):
            return {"output": res.get("message"), "exit_code": 0, "result": res}
        return {"output": f"Error: {res.get('error')}", "exit_code": 1, "result": res}

class UpdateFileFsTool:
    async def execute(self, content: str, ctx: dict) -> dict:
        args = _parse_tool_args(content)
        path = args.get("path")
        body = args.get("content", "")
        mode = args.get("mode", "overwrite")
        fs = get_filesystem_service()
        res = fs.update_file(path, body, mode)
        if res.get("success"):
            return {"output": res.get("message"), "exit_code": 0, "result": res}
        return {"output": f"Error: {res.get('error')}", "exit_code": 1, "result": res}

class DeleteFileFsTool:
    async def execute(self, content: str, ctx: dict) -> dict:
        args = _parse_tool_args(content)
        path = args.get("path")
        confirmed = args.get("confirmed", False)
        fs = get_filesystem_service()
        res = fs.delete_file(path, confirmed)
        if res.get("confirmation_required"):
            return {"output": f"CONFIRMATION REQUIRED: Are you sure you want to permanently delete '{res.get('path')}'? Reply with confirmed: true to proceed.", "exit_code": 0, "result": res}
        if res.get("success"):
            return {"output": res.get("message"), "exit_code": 0, "result": res}
        return {"output": f"Error: {res.get('error')}", "exit_code": 1, "result": res}

class DeleteDirectoryFsTool:
    async def execute(self, content: str, ctx: dict) -> dict:
        args = _parse_tool_args(content)
        path = args.get("path")
        recursive = args.get("recursive", False)
        confirmed = args.get("confirmed", False)
        fs = get_filesystem_service()
        res = fs.delete_directory(path, recursive, confirmed)
        if res.get("confirmation_required"):
            return {"output": f"CONFIRMATION REQUIRED: Are you sure you want to delete directory '{res.get('path')}' (recursive={recursive})? Reply with confirmed: true to proceed.", "exit_code": 0, "result": res}
        if res.get("success"):
            return {"output": res.get("message"), "exit_code": 0, "result": res}
        return {"output": f"Error: {res.get('error')}", "exit_code": 1, "result": res}

class RenameFileFsTool:
    async def execute(self, content: str, ctx: dict) -> dict:
        args = _parse_tool_args(content)
        src = args.get("src") or args.get("path")
        new_name = args.get("new_name") or args.get("name")
        fs = get_filesystem_service()
        res = fs.rename_file(src, new_name)
        if res.get("success"):
            return {"output": res.get("message"), "exit_code": 0, "result": res}
        return {"output": f"Error: {res.get('error')}", "exit_code": 1, "result": res}

class MoveFileFsTool:
    async def execute(self, content: str, ctx: dict) -> dict:
        args = _parse_tool_args(content)
        src = args.get("src") or args.get("path")
        dest = args.get("dest")
        confirmed = args.get("confirmed", False)
        fs = get_filesystem_service()
        res = fs.move_file(src, dest, confirmed)
        if res.get("confirmation_required"):
            return {"output": f"CONFIRMATION REQUIRED: Move '{res.get('src')}' to '{res.get('dest')}'? Reply with confirmed: true to proceed.", "exit_code": 0, "result": res}
        if res.get("success"):
            return {"output": res.get("message"), "exit_code": 0, "result": res}
        return {"output": f"Error: {res.get('error')}", "exit_code": 1, "result": res}

class CopyFileFsTool:
    async def execute(self, content: str, ctx: dict) -> dict:
        args = _parse_tool_args(content)
        src = args.get("src") or args.get("path")
        dest = args.get("dest")
        fs = get_filesystem_service()
        res = fs.copy_file(src, dest)
        if res.get("success"):
            return {"output": res.get("message"), "exit_code": 0, "result": res}
        return {"output": f"Error: {res.get('error')}", "exit_code": 1, "result": res}

class FileExistsFsTool:
    async def execute(self, content: str, ctx: dict) -> dict:
        args = _parse_tool_args(content)
        path = args.get("path")
        fs = get_filesystem_service()
        res = fs.file_exists(path)
        if res.get("success"):
            msg = f"Path '{res.get('path')}' {'EXISTS' if res.get('exists') else 'DOES NOT EXIST'}."
            return {"output": msg, "exit_code": 0, "result": res}
        return {"output": f"Error: {res.get('error')}", "exit_code": 1, "result": res}

class GetFileInfoFsTool:
    async def execute(self, content: str, ctx: dict) -> dict:
        args = _parse_tool_args(content)
        path = args.get("path")
        fs = get_filesystem_service()
        res = fs.get_file_info(path)
        if res.get("success"):
            out = f"File Info: {res.get('name')}\nPath: {res.get('path')}\nType: {'Directory' if res.get('is_dir') else ('Text' if res.get('is_text') else 'Binary')}\nSize: {res.get('size')} bytes\nCreated: {res.get('created')}\nModified: {res.get('modified')}"
            return {"output": out, "exit_code": 0, "result": res}
        return {"output": f"Error: {res.get('error')}", "exit_code": 1, "result": res}
