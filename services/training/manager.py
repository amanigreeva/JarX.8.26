import json
import logging
import uuid
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from .models import (
    TrainingJobInfo, TrainingMode, TrainingJobStatus, 
    TrainingConfig, CheckpointInfo, DatasetInfo
)
from .local_engine import LocalTrainingEngine
from .remote_engine import RemoteTrainingEngine
from src.constants import DATA_DIR
from core.database import SessionLocal, get_db_session

logger = logging.getLogger(__name__)

class TrainingManager:
    def __init__(self):
        self.base_dir = Path(DATA_DIR) / "training"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.base_dir / "jobs_index.json"
        self.local_engine = LocalTrainingEngine()
        self.remote_engine = RemoteTrainingEngine()
        self._init_index()

    def _init_index(self):
        if not self.index_file.exists():
            with open(self.index_file, "w") as f:
                json.dump({}, f)

    def _load_index(self) -> Dict[str, Any]:
        try:
            with open(self.index_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load jobs index: {e}")
            return {}

    def _save_index(self, index_data: Dict[str, Any]):
        try:
            with open(self.index_file, "w") as f:
                json.dump(index_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save jobs index: {e}")

    def _save_job_state(self, job_info: TrainingJobInfo):
        job_dir = self.base_dir / job_info.job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        job_file = job_dir / "job.json"
        try:
            with open(job_file, "w") as f:
                f.write(job_info.model_dump_json(indent=2))
                
            index = self._load_index()
            index[job_info.job_id] = {
                "name": job_info.name,
                "status": job_info.status.value,
                "mode": job_info.mode.value,
                "updated_at": job_info.updated_at.isoformat()
            }
            self._save_index(index)
        except Exception as e:
            logger.error(f"Failed to save job state for {job_info.job_id}: {e}")

    def _load_job_state(self, job_id: str) -> Optional[TrainingJobInfo]:
        job_file = self.base_dir / job_id / "job.json"
        if not job_file.exists():
            return None
        try:
            with open(job_file, "r") as f:
                data = json.load(f)
            return TrainingJobInfo(**data)
        except Exception as e:
            logger.error(f"Failed to load job state for {job_id}: {e}")
            return None

    def create_job(self, name: str, mode: Any, config: Any, owner: Optional[str] = None) -> TrainingJobInfo:
        if isinstance(config, dict):
            config = TrainingConfig(**config)
        if isinstance(mode, str):
            mode = TrainingMode(mode)
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        
        job_info = TrainingJobInfo(
            job_id=job_id,
            name=name,
            mode=mode,
            status=TrainingJobStatus.CREATED,
            config=config,
            total_epochs=config.epochs,
            created_at=now,
            updated_at=now,
            hardware_info=self.detect_hardware(),
            checkpoint_dir=str(self.base_dir / job_id / "checkpoints")
        )
        self._save_job_state(job_info)
        return job_info

    def start_job(self, job_id: str) -> Optional[TrainingJobInfo]:
        job_info = self._load_job_state(job_id)
        if not job_info:
            return None
            
        if job_info.mode == TrainingMode.LOCAL:
            success = self.local_engine.start_training(job_id, job_info.config)
            if success:
                job_info.status = TrainingJobStatus.STARTING
                job_info.started_at = datetime.now(timezone.utc)
            else:
                job_info.status = TrainingJobStatus.FAILED
                job_info.error = "Failed to start local training process"
        else:
            job_info.status = TrainingJobStatus.FAILED
            job_info.error = "Remote training not implemented"
            
        job_info.updated_at = datetime.now(timezone.utc)
        self._save_job_state(job_info)
        return job_info

    def pause_job(self, job_id: str) -> Optional[TrainingJobInfo]:
        job_info = self._load_job_state(job_id)
        if not job_info:
            return None
            
        if job_info.mode == TrainingMode.LOCAL:
            if self.local_engine.pause_training(job_id):
                job_info.status = TrainingJobStatus.PAUSED
        
        job_info.updated_at = datetime.now(timezone.utc)
        self._save_job_state(job_info)
        return job_info

    def resume_job(self, job_id: str) -> Optional[TrainingJobInfo]:
        job_info = self._load_job_state(job_id)
        if not job_info:
            return None
            
        if job_info.mode == TrainingMode.LOCAL:
            if self.local_engine.resume_training(job_id):
                job_info.status = TrainingJobStatus.RUNNING
                
        job_info.updated_at = datetime.now(timezone.utc)
        self._save_job_state(job_info)
        return job_info

    def stop_job(self, job_id: str) -> Optional[TrainingJobInfo]:
        job_info = self._load_job_state(job_id)
        if not job_info:
            return None
            
        if job_info.mode == TrainingMode.LOCAL:
            if self.local_engine.stop_training(job_id):
                job_info.status = TrainingJobStatus.STOPPED
                job_info.finished_at = datetime.now(timezone.utc)
                
        job_info.updated_at = datetime.now(timezone.utc)
        self._save_job_state(job_info)
        return job_info

    def cancel_job(self, job_id: str) -> Optional[TrainingJobInfo]:
        job_info = self.stop_job(job_id)
        if job_info:
            job_info.status = TrainingJobStatus.CANCELLED
            job_info.updated_at = datetime.now(timezone.utc)
            self._save_job_state(job_info)
        return job_info

    def get_job(self, job_id: str) -> Optional[TrainingJobInfo]:
        job_info = self._load_job_state(job_id)
        if not job_info:
            return None
            
        if job_info.mode == TrainingMode.LOCAL and job_info.status in (TrainingJobStatus.STARTING, TrainingJobStatus.RUNNING):
            engine_status = self.local_engine.get_status(job_id)
            if "status" in engine_status:
                try:
                    job_info.status = TrainingJobStatus(engine_status["status"])
                except ValueError:
                    pass
            if "current_epoch" in engine_status:
                job_info.current_epoch = engine_status["current_epoch"]
                
            self._save_job_state(job_info)
            
        return job_info

    def list_jobs(self, owner: Optional[str] = None, status: Optional[TrainingJobStatus] = None) -> List[TrainingJobInfo]:
        index = self._load_index()
        jobs = []
        for job_id in index:
            job_info = self.get_job(job_id)
            if job_info:
                if status and job_info.status != status:
                    continue
                jobs.append(job_info)
        return jobs

    def get_logs(self, job_id: str, tail: int = 50) -> List[str]:
        job_info = self._load_job_state(job_id)
        if not job_info:
            return []
        if job_info.mode == TrainingMode.LOCAL:
            return self.local_engine.get_logs(job_id, tail)
        return []

    def get_metrics(self, job_id: str) -> dict:
        job_info = self._load_job_state(job_id)
        if not job_info:
            return {}
        if job_info.mode == TrainingMode.LOCAL:
            return self.local_engine.get_metrics(job_id)
        return {}

    def list_checkpoints(self, job_id: str) -> List[CheckpointInfo]:
        job_info = self._load_job_state(job_id)
        if not job_info:
            return []
        if job_info.mode == TrainingMode.LOCAL:
            return self.local_engine.list_checkpoints(job_id)
        return []

    def restore_checkpoint(self, job_id: str, checkpoint_path: str) -> bool:
        # Placeholder for restore logic
        return False

    def sync_results(self, job_id: str) -> dict:
        # Placeholder for sync logic
        return {}

    def detect_hardware(self) -> dict:
        return self.local_engine.detect_hardware()

    def get_dataset_info(self, dataset_path: str) -> DatasetInfo:
        path = Path(dataset_path)
        size_bytes = 0
        file_hash = "unknown"
        if path.exists():
            if path.is_file():
                size_bytes = path.stat().st_size
                with open(path, "rb") as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
            elif path.is_dir():
                for f in path.rglob("*"):
                    if f.is_file():
                        size_bytes += f.stat().st_size
                        
        return DatasetInfo(
            dataset_id=uuid.uuid4().hex[:8],
            path=str(path),
            file_hash=file_hash,
            size_bytes=size_bytes,
            version="1.0",
            metadata={}
        )
