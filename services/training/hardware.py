"""
hardware.py

Detect local hardware capabilities for AI training.
Handles missing psutil and torch gracefully.
"""

import os
import platform
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

try:
    import psutil
    _HAS_PSUTIL = True
except ImportError:
    _HAS_PSUTIL = False
    logger.info("psutil not installed; RAM detection will be approximate")


def detect_hardware() -> Dict[str, Any]:
    """Detect local hardware capabilities for training.
    
    Returns a dict with cpu, ram_total_gb, ram_available_gb,
    gpu_available, gpu_name, gpu_vram_gb, cuda_version, pytorch_cuda.
    Gracefully handles missing psutil and torch.
    """
    info: Dict[str, Any] = {
        "cpu": platform.processor() or platform.machine() or "Unknown",
        "cpu_cores": os.cpu_count() or 1,
        "ram_total_gb": 0.0,
        "ram_available_gb": 0.0,
        "gpu_available": False,
        "gpu_name": None,
        "gpu_count": 0,
        "gpu_vram_gb": None,
        "cuda_version": None,
        "pytorch_cuda": False,
        "platform": platform.system(),
        "python_version": platform.python_version(),
    }

    # RAM detection
    if _HAS_PSUTIL:
        try:
            mem = psutil.virtual_memory()
            info["ram_total_gb"] = round(mem.total / (1024 ** 3), 1)
            info["ram_available_gb"] = round(mem.available / (1024 ** 3), 1)
        except Exception as e:
            logger.warning(f"psutil RAM detection failed: {e}")
    else:
        # Fallback: try to read from OS
        try:
            if platform.system() == "Windows":
                import ctypes
                kernel32 = ctypes.windll.kernel32
                c_ulonglong = ctypes.c_ulonglong

                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ("dwLength", ctypes.c_ulong),
                        ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", c_ulonglong),
                        ("ullAvailPhys", c_ulonglong),
                        ("ullTotalPageFile", c_ulonglong),
                        ("ullAvailPageFile", c_ulonglong),
                        ("ullTotalVirtual", c_ulonglong),
                        ("ullAvailVirtual", c_ulonglong),
                        ("ullAvailExtendedVirtual", c_ulonglong),
                    ]

                stat = MEMORYSTATUSEX()
                stat.dwLength = ctypes.sizeof(stat)
                kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
                info["ram_total_gb"] = round(stat.ullTotalPhys / (1024 ** 3), 1)
                info["ram_available_gb"] = round(stat.ullAvailPhys / (1024 ** 3), 1)
        except Exception as e:
            logger.debug(f"Fallback RAM detection failed: {e}")

    # GPU detection via torch
    try:
        import torch
        info["pytorch_cuda"] = torch.cuda.is_available()
        if torch.cuda.is_available():
            info["gpu_available"] = True
            info["gpu_count"] = torch.cuda.device_count()
            info["gpu_name"] = torch.cuda.get_device_name(0) if torch.cuda.device_count() > 0 else None
            info["cuda_version"] = torch.version.cuda
            try:
                props = torch.cuda.get_device_properties(0)
                info["gpu_vram_gb"] = round(props.total_mem / (1024 ** 3), 1)
            except Exception:
                pass
    except ImportError:
        logger.info("PyTorch not installed — GPU detection unavailable")
    except Exception as e:
        logger.warning(f"GPU detection error: {e}")

    return info


# Legacy alias used by local_engine
get_hardware_info = detect_hardware
