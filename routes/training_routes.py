from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Any
import logging

from services.training import get_training_manager

logger = logging.getLogger(__name__)

class CreateJobReq(BaseModel):
    name: str
    mode: str
    config: dict

class RestoreJobReq(BaseModel):
    checkpoint_path: str

def setup_training_routes():
    router = APIRouter(prefix="/api/training", tags=["training"])

    @router.post("/jobs")
    async def create_job(req: CreateJobReq):
        manager = get_training_manager()
        try:
            res = manager.create_job(name=req.name, mode=req.mode, config=req.config)
            return res
        except Exception as e:
            logger.error(f"Error creating job: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/jobs")
    async def list_jobs(status: Optional[str] = None, owner: Optional[str] = None):
        manager = get_training_manager()
        try:
            res = manager.list_jobs(status=status, owner=owner)
            return res
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/jobs/{job_id}")
    async def get_job(job_id: str):
        manager = get_training_manager()
        try:
            res = manager.get_job(job_id)
            if not res:
                raise HTTPException(status_code=404, detail="Job not found")
            return res
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/jobs/{job_id}/start")
    async def start_job(job_id: str):
        manager = get_training_manager()
        try:
            res = manager.start_job(job_id)
            return res
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/jobs/{job_id}/pause")
    async def pause_job(job_id: str):
        manager = get_training_manager()
        try:
            res = manager.pause_job(job_id)
            return res
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/jobs/{job_id}/resume")
    async def resume_job(job_id: str):
        manager = get_training_manager()
        try:
            res = manager.resume_job(job_id)
            return res
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/jobs/{job_id}/stop")
    async def stop_job(job_id: str):
        manager = get_training_manager()
        try:
            res = manager.stop_job(job_id)
            return res
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/jobs/{job_id}/cancel")
    async def cancel_job(job_id: str):
        manager = get_training_manager()
        try:
            res = manager.cancel_job(job_id)
            return res
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/jobs/{job_id}/logs")
    async def get_logs(job_id: str, tail: int = 50):
        manager = get_training_manager()
        try:
            res = manager.get_logs(job_id, tail=tail)
            return res
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/jobs/{job_id}/metrics")
    async def get_metrics(job_id: str):
        manager = get_training_manager()
        try:
            res = manager.get_metrics(job_id)
            return res
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/jobs/{job_id}/checkpoints")
    async def list_checkpoints(job_id: str):
        manager = get_training_manager()
        try:
            res = manager.list_checkpoints(job_id)
            return res
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/jobs/{job_id}/restore")
    async def restore_job(job_id: str, req: RestoreJobReq):
        manager = get_training_manager()
        try:
            res = manager.restore_job(job_id, req.checkpoint_path)
            return res
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/jobs/{job_id}/sync")
    async def sync_job(job_id: str):
        manager = get_training_manager()
        try:
            res = manager.sync_job(job_id)
            return res
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/hardware")
    async def detect_hardware():
        manager = get_training_manager()
        try:
            res = manager.detect_hardware()
            return res
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.delete("/jobs/{job_id}")
    async def delete_job(job_id: str):
        manager = get_training_manager()
        try:
            res = manager.delete_job(job_id)
            return res
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    return router
