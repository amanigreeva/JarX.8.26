from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime

class TrainingJobStatus(str, Enum):
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    PROVISIONING = "PROVISIONING"
    UPLOADING = "UPLOADING"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    RESUMING = "RESUMING"
    SYNCING = "SYNCING"
    RECOVERABLE = "RECOVERABLE"

class TrainingMode(str, Enum):
    LOCAL = "local"
    REMOTE = "remote"

class TrainingConfig(BaseModel):
    model_path: Optional[str] = None
    dataset_path: Optional[str] = None
    epochs: int = 10
    batch_size: int = 32
    learning_rate: float = 0.001
    mixed_precision: bool = False
    checkpoint_interval: int = 1
    max_runtime_hours: Optional[float] = None
    max_gpu_hours: Optional[float] = None
    output_dir: Optional[str] = None
    metrics: List[str] = Field(default_factory=list)
    extra_args: Dict[str, Any] = Field(default_factory=dict)

class CheckpointInfo(BaseModel):
    path: str
    epoch: int
    global_step: int
    loss: float
    created_at: datetime
    size_bytes: int
    is_valid: bool

class ExperimentInfo(BaseModel):
    experiment_id: str
    job_id: str
    hyperparameters: Dict[str, Any]
    metrics_summary: Dict[str, Any]
    best_metric: float
    git_commit: Optional[str] = None
    created_at: datetime

class DatasetInfo(BaseModel):
    dataset_id: str
    path: str
    file_hash: str
    size_bytes: int
    version: str
    metadata: Dict[str, Any]

class TrainingJobInfo(BaseModel):
    job_id: str
    name: str
    mode: TrainingMode
    status: TrainingJobStatus
    config: TrainingConfig
    current_epoch: int = 0
    total_epochs: int = 0
    metrics: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    checkpoint_dir: Optional[str] = None
    remote_host: Optional[str] = None
    remote_job_id: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    hardware_info: Dict[str, Any] = Field(default_factory=dict)
    experiment_id: Optional[str] = None
