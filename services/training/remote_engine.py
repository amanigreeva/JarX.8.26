import logging
from typing import Dict, Any, List, Optional
from .models import TrainingConfig, DatasetInfo

logger = logging.getLogger(__name__)

class RemoteTrainingEngine:
    def _raise_not_configured(self):
        raise NotImplementedError("Remote training server not configured. Set JARX_REMOTE_TRAINING_HOST in .env")

    def check_connection(self, host: str, port: int = 8443, auth: Optional[str] = None) -> bool:
        try:
            self._raise_not_configured()
        except NotImplementedError:
            return False
        return False

    def submit_job(self, host: str, config: TrainingConfig, dataset_info: DatasetInfo) -> str:
        self._raise_not_configured()
        return ""

    def get_remote_status(self, host: str, remote_job_id: str) -> Dict[str, Any]:
        self._raise_not_configured()
        return {}

    def get_remote_logs(self, host: str, remote_job_id: str, tail: int = 50) -> List[str]:
        self._raise_not_configured()
        return []

    def sync_results(self, host: str, remote_job_id: str, local_dir: str) -> Dict[str, Any]:
        self._raise_not_configured()
        return {}

    def cancel_remote_job(self, host: str, remote_job_id: str) -> bool:
        self._raise_not_configured()
        return False
