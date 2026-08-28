import json
from services.training import get_training_manager

def _parse_tool_args(content: str) -> dict:
    text = str(content or "").strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except Exception:
        return {}

class CreateTrainingJobTool:
    def execute(self, tool_input: str, **kwargs) -> str:
        """Create a new training job."""
        try:
            args = _parse_tool_args(tool_input)
            name = args.get("name")
            mode = args.get("mode")
            config = args.get("config", args)
            manager = get_training_manager()
            res = manager.create_job(name=name, mode=mode, config=config)
            return json.dumps(res)
        except Exception as e:
            return json.dumps({"error": str(e)})

class StartTrainingTool:
    def execute(self, tool_input: str, **kwargs) -> str:
        try:
            args = _parse_tool_args(tool_input)
            job_id = args.get("job_id")
            manager = get_training_manager()
            res = manager.start_job(job_id)
            return json.dumps(res)
        except Exception as e:
            return json.dumps({"error": str(e)})

class StopTrainingTool:
    def execute(self, tool_input: str, **kwargs) -> str:
        try:
            args = _parse_tool_args(tool_input)
            job_id = args.get("job_id")
            manager = get_training_manager()
            res = manager.stop_job(job_id)
            return json.dumps(res)
        except Exception as e:
            return json.dumps({"error": str(e)})

class GetTrainingStatusTool:
    def execute(self, tool_input: str, **kwargs) -> str:
        try:
            args = _parse_tool_args(tool_input)
            job_id = args.get("job_id")
            manager = get_training_manager()
            res = manager.get_job(job_id)
            return json.dumps(res)
        except Exception as e:
            return json.dumps({"error": str(e)})

class ListTrainingJobsTool:
    def execute(self, tool_input: str, **kwargs) -> str:
        try:
            args = _parse_tool_args(tool_input)
            status = args.get("status")
            manager = get_training_manager()
            res = manager.list_jobs(status=status)
            return json.dumps(res)
        except Exception as e:
            return json.dumps({"error": str(e)})

class GetTrainingLogsTool:
    def execute(self, tool_input: str, **kwargs) -> str:
        try:
            args = _parse_tool_args(tool_input)
            job_id = args.get("job_id")
            tail = args.get("tail", 50)
            manager = get_training_manager()
            res = manager.get_logs(job_id, tail=tail)
            return json.dumps(res)
        except Exception as e:
            return json.dumps({"error": str(e)})

class GetTrainingMetricsTool:
    def execute(self, tool_input: str, **kwargs) -> str:
        try:
            args = _parse_tool_args(tool_input)
            job_id = args.get("job_id")
            manager = get_training_manager()
            res = manager.get_metrics(job_id)
            return json.dumps(res)
        except Exception as e:
            return json.dumps({"error": str(e)})

class DetectHardwareTool:
    def execute(self, tool_input: str, **kwargs) -> str:
        try:
            manager = get_training_manager()
            res = manager.detect_hardware()
            return json.dumps(res)
        except Exception as e:
            return json.dumps({"error": str(e)})
