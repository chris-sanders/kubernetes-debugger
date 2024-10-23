# llm_handlers/base.py
from abc import ABC, abstractmethod
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

class BaseLLMHandler(ABC):
    def __init__(self, model: str, api_key: str) -> None:
        self.model = model
        self.api_key = api_key
        self.client = self._initialize_client()
        self.kubectl_tool_definition = self._get_kubectl_tool_definition()
        self.system_prompt = """You are a Kubernetes cluster debugging assistant. 
            You have read-only access to the cluster through kubectl commands.
            Analyze issues and provide clear explanations.
            When you need information, use kubectl commands through the provided function."""
        self.messages = None  # Will store conversation history

    @abstractmethod
    def _initialize_client(self):
        """Initialize the specific LLM client"""
        pass

    @abstractmethod
    def _get_kubectl_tool_definition(self) -> Dict:
        """Return provider-specific tool/function definition"""
        pass

    @abstractmethod
    def _create_completion(self, messages: List[Dict]) -> Any:
        """Make the actual API call to the LLM provider"""
        pass

    @abstractmethod
    def _handle_tool_response(self, response: Any) -> Tuple[bool, List[Dict], str]:
        """
        Handle the tool response from the LLM
        Returns: (has_tool_calls: bool, new_messages: List[Dict], final_response: str)
        """
        pass

    def _execute_kubectl(self, command: str) -> Tuple[str, str, int]:
        """Execute kubectl command and handle results"""
        from kubectl_handler import execute_kubectl_command
        logger.info(f"Executing kubectl command: {command}")
        return execute_kubectl_command(command)

    def process_query(self, query: str) -> str:
        # Initialize messages only if this is the first query
        if self.messages is None:
            self.messages = self._initialize_messages(query)
        else:
            # Add new query to existing conversation
            self.messages.append({"role": "user", "content": query})

        while True:
            logger.info(f"Sending request to {self.__class__.__name__}...")
            logger.debug(f"Messages: {self.messages}")

            response = self._create_completion(self.messages)
            has_tool_calls, new_messages, final_response = self._handle_tool_response(response)

            if has_tool_calls:
                self.messages.extend(new_messages)
            else:
                # Add assistant's final response to history
                self.messages.append({"role": "assistant", "content": final_response})
                return final_response

    def reset_conversation(self):
        """Method to explicitly clear conversation history"""
        self.messages = None

    def get_conversation_history(self) -> List[Dict]:
        """Return the current conversation history"""
        return self.messages if self.messages else []
