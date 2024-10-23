# kubectl_handler.py
import subprocess
from typing import Tuple
import logging

logger = logging.getLogger(__name__)

def execute_kubectl_command(command: str) -> Tuple[str, str, int]:
    """Execute a kubectl command and return stdout, stderr, and return code"""
    logger.info(f"Executing kubectl command: kubectl {command}")
    
    process = subprocess.Popen(
        f"kubectl {command}",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    stdout, stderr = process.communicate()
    logger.debug(f"Command output:\n{stdout}")
    if stderr:
        logger.debug(f"Command stderr:\n{stderr}")
    return stdout, stderr, process.returncode
