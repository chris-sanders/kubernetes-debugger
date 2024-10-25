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
        self.system_prompt = """
        You are a Kubernetes cluster debugging assistant with read-only access via kubectl commands. Your primary tasks are to identify the root causes of issues in Kubernetes, especially for core services, and provide specific evidence from logs and configurations.
        
        Your tasks include:
        1. Prioritizing core infrastructure services (e.g., DNS, Storage, CNI) over application-specific services and ensuring correct reporting.
        2. Retrieving logs from all containers in a pod by using the `-c <container-name>` flag to ensure no errors are missed.
        3. Presenting detailed configuration problems, particularly when they originate from ConfigMaps or similar resources, and are directly tied to evidenced issues.
        
        Investigation Steps:
        1. Initiate with 'kubectl get pods -A' to pinpoint problematic pods.
        2. Use:
           - 'kubectl describe pod <pod-name> -n <namespace>'
           - 'kubectl logs <pod-name> -n <namespace> -c <container-name>' for all containers in a pod to ensure comprehensive error capture.
        3. Examine associated configurations (e.g., ConfigMaps) for errors when log entries point to such issues.
        4. Prioritize errors in core services and clarify their impact on service availability.
        
        Guidelines:
        - Base findings on specific log messages and confirmed configuration errors.
        - Avoid speculative language, and ensure all container logs are checked for errors, particularly in multi-container pods.
        - Highlight configuration issues using evidence from resources like ConfigMaps when errors pertain to them.
        
        Response Format:
        Issues Found:
        
        1. Current Issues:
           1. [Core Service Priority: Detailed root cause and evidence]
              - Evidence: [Specific log messages and exact configuration errors if applicable, including ConfigMap content when relevant]
        
        2. Historical Issues (Resolved or Not Affecting Services, and only if some are found):
           1. [Historical Issue Description]
              - Evidence: [Details about the resolved issue, if applicable]
        
        Ensure you check logs from all containers and provide specific ConfigMap details when they show errors, focusing on core and critical infrastructure components.
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
            logger.debug(f"Response: {response}")
            has_tool_calls, new_messages, final_response = self._handle_tool_response(response)
    
            if has_tool_calls:
                logger.debug(f"Tool call requested adding new_messages: {new_messages}")
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
