from .manager import TrainingManager

_manager = None

def get_training_manager() -> TrainingManager:
    global _manager
    if _manager is None:
        _manager = TrainingManager()
    return _manager

__all__ = ["get_training_manager", "TrainingManager"]
