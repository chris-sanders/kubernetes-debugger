# kubectl_handler.py
import subprocess
from typing import Tuple
import logging

logger = logging.getLogger(__name__)

def truncate_logs(log_content: str, lines_per_section: int = 100) -> str:
    """
    Keep the first and last N lines of logs with a summary of what was removed.
    """
    log_lines = log_content.splitlines()
    if len(log_lines) <= lines_per_section * 2:
        return log_content
        
    head_section = log_lines[:lines_per_section]
    tail_section = log_lines[-lines_per_section:]
    removed_lines = len(log_lines) - (lines_per_section * 2)
    
    truncated_log = (
        "=== Log Start ===\n"
        f"{'\n'.join(head_section)}\n"
        f"\n[... {removed_lines:,} lines removed ...]\n\n"
        f"{'\n'.join(tail_section)}\n"
        "=== Log End ==="
    )
    
    return truncated_log

def execute_kubectl_command(command: str) -> Tuple[str, str, int]:
    """Execute a kubectl command and return stdout, stderr, and return code"""
    clean_command = command.replace('kubectl ', '').strip()
    
    logger.info(f"Executing kubectl command: kubectl {clean_command}")
    
    process = subprocess.Popen(
        f"kubectl {clean_command}",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    stdout, stderr = process.communicate()
    
    # Only truncate if it's a logs command
    if 'logs' in clean_command:
        stdout = truncate_logs(stdout)
        if stderr:
            stderr = truncate_logs(stderr)
    
    logger.debug(f"Command output:\n{stdout}")
    if stderr:
        logger.debug(f"Command stderr:\n{stderr}")
    return stdout, stderr, process.returncode
