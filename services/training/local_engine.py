import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from .hardware import get_hardware_info
from .models import TrainingConfig, CheckpointInfo
from src.constants import DATA_DIR

logger = logging.getLogger(__name__)

class LocalTrainingEngine:
    def __init__(self):
        self.training_dir = Path(DATA_DIR) / "training"
        self.training_dir.mkdir(parents=True, exist_ok=True)
        self.processes: Dict[str, subprocess.Popen] = {}

    def detect_hardware(self) -> Dict[str, Any]:
        return get_hardware_info()

    def start_training(self, job_id: str, config: TrainingConfig) -> bool:
        job_dir = self.training_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup directories
        checkpoints_dir = job_dir / "checkpoints"
        checkpoints_dir.mkdir(exist_ok=True)
        final_model_dir = job_dir / "final_model"
        final_model_dir.mkdir(exist_ok=True)

        # Write config
        config_path = job_dir / "config.json"
        with open(config_path, "w") as f:
            f.write(config.model_dump_json(indent=2))

        # Generate script
        script_path = job_dir / "train_script.py"
        script_content = self._generate_training_script(job_id, config)
        with open(script_path, "w") as f:
            f.write(script_content)

        # Initialize status
        status_path = job_dir / "status.json"
        with open(status_path, "w") as f:
            json.dump({"status": "STARTING", "current_epoch": 0}, f)

        # Launch process
        log_path = job_dir / "train.log"
        try:
            with open(log_path, "w") as log_file:
                proc = subprocess.Popen(
                    ["python", str(script_path)],
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    cwd=str(job_dir)
                )
            self.processes[job_id] = proc
            return True
        except Exception as e:
            logger.error(f"Failed to start training for {job_id}: {e}")
            return False

    def pause_training(self, job_id: str) -> bool:
        job_dir = self.training_dir / job_id
        pause_flag = job_dir / "pause_flag"
        try:
            pause_flag.touch()
            return True
        except Exception as e:
            logger.error(f"Failed to pause training for {job_id}: {e}")
            return False

    def resume_training(self, job_id: str) -> bool:
        job_dir = self.training_dir / job_id
        pause_flag = job_dir / "pause_flag"
        try:
            if pause_flag.exists():
                pause_flag.unlink()
            return True
        except Exception as e:
            logger.error(f"Failed to resume training for {job_id}: {e}")
            return False

    def stop_training(self, job_id: str) -> bool:
        proc = self.processes.get(job_id)
        if proc:
            try:
                proc.terminate()
                proc.wait(timeout=5)
                return True
            except subprocess.TimeoutExpired:
                proc.kill()
                return True
            except Exception as e:
                logger.error(f"Failed to stop training for {job_id}: {e}")
                return False
        return False

    def get_status(self, job_id: str) -> dict:
        status_path = self.training_dir / job_id / "status.json"
        if not status_path.exists():
            return {}
        try:
            with open(status_path, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def get_logs(self, job_id: str, tail: int = 50) -> List[str]:
        log_path = self.training_dir / job_id / "train.log"
        if not log_path.exists():
            return []
        try:
            with open(log_path, "r") as f:
                lines = f.readlines()
            return [line.strip() for line in lines[-tail:]]
        except Exception:
            return []

    def get_metrics(self, job_id: str) -> dict:
        metrics_path = self.training_dir / job_id / "metrics.json"
        if not metrics_path.exists():
            return {}
        try:
            with open(metrics_path, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def list_checkpoints(self, job_id: str) -> List[CheckpointInfo]:
        checkpoints_dir = self.training_dir / job_id / "checkpoints"
        if not checkpoints_dir.exists():
            return []
        
        checkpoints = []
        try:
            for pt_file in checkpoints_dir.glob("*.pt"):
                stat = pt_file.stat()
                # Parse epoch from name e.g., checkpoint_001.pt
                epoch = 0
                if "checkpoint_" in pt_file.name:
                    try:
                        epoch = int(pt_file.stem.split("_")[-1])
                    except ValueError:
                        pass
                        
                checkpoints.append(CheckpointInfo(
                    path=str(pt_file),
                    epoch=epoch,
                    global_step=epoch * 100, # Mock
                    loss=0.0, # Mock
                    created_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
                    size_bytes=stat.st_size,
                    is_valid=True
                ))
        except Exception as e:
            logger.error(f"Error listing checkpoints for {job_id}: {e}")
            
        return sorted(checkpoints, key=lambda x: x.epoch)

    def _generate_training_script(self, job_id: str, config: TrainingConfig) -> str:
        return f"""
import time
import json
import os
import signal
import sys
from pathlib import Path

# Paths
BASE_DIR = Path.cwd()
CHECKPOINT_DIR = BASE_DIR / "checkpoints"
STATUS_FILE = BASE_DIR / "status.json"
METRICS_FILE = BASE_DIR / "metrics.json"
PAUSE_FLAG = BASE_DIR / "pause_flag"

def update_status(status, epoch):
    with open(STATUS_FILE, "w") as f:
        json.dump({{"status": status, "current_epoch": epoch}}, f)

def write_metrics(metrics):
    try:
        if METRICS_FILE.exists():
            with open(METRICS_FILE, "r") as f:
                data = json.load(f)
        else:
            data = []
        data.append(metrics)
        with open(METRICS_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Error writing metrics: {{e}}")

def handle_sigterm(signum, frame):
    print("Received SIGTERM, stopping training.")
    update_status("STOPPED", current_epoch)
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_sigterm)

print("Starting training job {job_id}...")
current_epoch = 0
total_epochs = {config.epochs}

update_status("RUNNING", current_epoch)

try:
    import torch
    print(f"PyTorch available: {{torch.__version__}}")
    has_torch = True
except ImportError:
    print("PyTorch not available, running in simulation mode.")
    has_torch = False

for epoch in range(1, total_epochs + 1):
    current_epoch = epoch
    print(f"Starting epoch {{epoch}}/{{total_epochs}}...")
    
    # Check pause
    while PAUSE_FLAG.exists():
        update_status("PAUSED", current_epoch - 1)
        time.sleep(5)
    
    update_status("RUNNING", current_epoch)
    
    # Simulate epoch time
    time.sleep(2)
    
    # Save checkpoint
    if epoch % {config.checkpoint_interval} == 0 or epoch == total_epochs:
        ckpt_path = CHECKPOINT_DIR / f"checkpoint_{{epoch:03d}}.pt"
        latest_path = CHECKPOINT_DIR / "latest.pt"
        if has_torch:
            torch.save({{"epoch": epoch}}, ckpt_path)
            torch.save({{"epoch": epoch}}, latest_path)
        else:
            with open(ckpt_path, "w") as f:
                f.write(f"simulated checkpoint {{epoch}}")
            with open(latest_path, "w") as f:
                f.write(f"simulated checkpoint {{epoch}}")
        print(f"Saved checkpoint to {{ckpt_path}}")
        
    # Write metrics
    write_metrics({{"epoch": epoch, "loss": 1.0 / epoch}})
    print(f"Completed epoch {{epoch}}")

update_status("COMPLETED", current_epoch)
print("Training completed successfully.")
"""
