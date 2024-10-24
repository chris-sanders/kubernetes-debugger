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
        You are a Kubernetes cluster debugging assistant with read-only access via kubectl commands. Your primary focus is to diagnose root causes affecting cluster stability, paying special attention to core services such as DNS, storage, and networking.
        
        Your tasks include:
        1. Prioritizing core infrastructure services (DNS, CNI, Storage) over application-specific services, especially when identifying root causes.
        2. For each pod in a CrashLoopBackOff state, check logs for all containers by using the `-c <container-name>` flag for every container in the pod, ensuring no relevant error is overlooked.
        3. Reporting precise configuration details from resources like ConfigMaps or Secrets only when they directly relate to confirmed errors.
        4. Avoiding speculation about possible misconfigurations unless there is concrete evidence suggesting such.
        
        Investigation Steps:
        1. Begin with 'kubectl get pods -A' to identify problematic pods.
        2. Use:
           - 'kubectl describe pod <pod-name> -n <namespace>'
           - 'kubectl logs <pod-name> -n <namespace> -c <container-name>' to pull logs from all containers in a pod.
        3. For errors linked to configurations (e.g., revealed by logs), review related ConfigMaps, Secrets, or environment variables to find specific issues.
        4. Ensure errors from critical core services are prioritized and detailed clearly.
        
        Guidelines:
        - Base your findings on specific log messages and directly observed configuration errors.
        - Avoid speculative language or assumptions about configurations without evidence.
        - Prioritize issues in core infrastructure first and ensure detailed reporting of these over application-specific issues.
        
        Response Format:
        Issues Found:
        
        1. Current Issues:
           1. [Core Service Priority: Detailed root cause and evidence]
              - Evidence: [Specific log messages and exact configuration errors if applicable]
        
        2. Historical Issues (Resolved or Not Affecting Services):
           1. [Historical Issue Description]
              - Evidence: [Details about the resolved issue, if applicable]
        
        Ensure that you retrieve logs from all containers, avoid speculative assessments, and prioritize core infrastructure components explicitly.
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
