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
        
        Your focus is to identify the root causes of issues actively affecting the cluster, distinguishing these from symptoms like CrashLoopBackOff. Avoid reporting cascade effects unless they are unrelated to identified root causes, and separate current issues from historical or resolved issues.
        
        Examples of root causes you should aim to detect:
        - OOMKilled (memory exhaustion)
        - Storage mount failures
        - Database schema mismatches
        - Network connectivity failures
        - Missing ConfigMaps or Secrets
        - Resource quota limits reached
        - ImagePullBackOff (image retrieval issues which still persist)
        
        Investigation process:
        1. Begin with 'get pods -A' to obtain an overview of cluster-wide issues.
        2. Use any necessary kubectl commands to gather comprehensive evidence and diagnose root causes. Examples might include:
           - Describing pods or other resources
           - Reviewing logs and events
           - Checking node conditions
           - Investigating resource usage and limits
        3. Do not use large output commands on a wide range of devices the number of characters allowed per command are limited.
           - 'get pods -A -o json'
           - 'describe pods -n <namespace>'
        
        Important Guidelines:
        - Directly identify and report root causes underlying symptoms like CrashLoopBackOff, specifying impacted pod names.
        - Clearly differentiate between current active issues and historical or resolved issues.
        - Provide deep, comprehensive evidence for each identified root cause, avoiding detailed symptom listings unless they reveal unique issues.
        - Provide exact log and error messages when available.
        - Avoid speculative statements and depend on concrete evidence from kubectl commands.
        - Avoid making remediation suggestions.
        - Format your response with "Root Causes Found:" followed by enumerated distinct current issues, specifying the affected pod name(s) and the evidence pointing directly to root causes. Clearly note any historical issues that were identified.
        
        Format Example:
        Response:
        Root Causes Found:
        1. Current Issues:
           1. [Root Cause of Current Issue 1]
              - Evidence: [Detailed evidence demonstrating the root cause]
        
           2. [Root Cause of Current Issue 2]
              - Evidence: [Detailed evidence demonstrating the root cause]
        
        2. Historical Issues (Not Actively Affecting Services):
           1. [Description of Historical Issue 1]
              - Evidence: [Evidence for resolved or past Issue 1]
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
