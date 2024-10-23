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
        self.messages = None  # Will store conversation history
        self.system_prompt = """You are a Kubernetes cluster debugging assistant. 
        You have read-only access to the cluster through kubectl commands.
        When investigating issues:
        1. Start with broad commands like `kubectl get po -A` to see what is happening 
        2. For detailed information, focus on specific pods or namespaces rather than requesting full cluster data
        3. Avoid using '-o json' for full cluster queries as it's too verbose
        4. Use targeted selectors, labels, or jsonpath when you need specific fields
        5. Review each failure, being sure to check pod logs for clues
        
        For example:
        - Use 'get pods -A' for cluster overview
        - Then narrow down with commands like:
          - 'describe pod <specific-pod> -n <namespace>'
          - 'logs <specific-pod> -n <namespace>'
          - 'get pods -n <namespace> -o jsonpath=...' (for specific fields)
        
        Only profide the top issues and no remediation steps.
        """


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
        if self.messages is None:
            self.messages = self._initialize_messages(query)
        else:
            self.messages.append({"role": "user", "content": query})
    
        while True:
            logger.info(f"Sending request to {self.__class__.__name__}...")
            logger.debug(f"Messages: {self.messages}")
            
            response = self._create_completion(self.messages)
            has_tool_calls, new_messages, final_response = self._handle_tool_response(response)
    
            if has_tool_calls:
                self.messages.extend(new_messages)
            else:
                # If we have a final response, append it and return immediately
                self.messages.append({"role": "assistant", "content": final_response})
                logger.info("Got final response, returning")
                return final_response

    def reset_conversation(self):
        """Method to explicitly clear conversation history"""
        self.messages = None

    def get_conversation_history(self) -> List[Dict]:
        """Return the current conversation history"""
        return self.messages if self.messages else []
