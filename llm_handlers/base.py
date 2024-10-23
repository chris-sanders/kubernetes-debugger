# llm_handlers/base.py
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class BaseLLMHandler(ABC):
    def __init__(self, model: str):
        self.model = model
        
    @abstractmethod
    def process_query(self, query: str) -> str:
        pass
