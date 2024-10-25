# llm_handlers/openai.py
from typing import List, Dict, Any, Tuple
import json
import logging
from openai import OpenAI
from .base import BaseLLMHandler
from kubectl_handler import execute_kubectl_command

logger = logging.getLogger("kubernetes-debugger")

class OpenAIHandler(BaseLLMHandler):
    def _initialize_client(self):
        return OpenAI(api_key=self.api_key)

    def _initialize_messages(self, query: str) -> List[Dict]:
        """OpenAI includes system message in the messages list"""
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": query}
        ]

    def _get_kubectl_tool_definition(self) -> Dict:
        return {
            "type": "function",
            "function": {
                "name": "run_kubectl",
                "description": "Run a kubectl command to inspect the kubernetes cluster",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The kubectl command to run (without 'kubectl' prefix)"
                        }
                    },
                    "required": ["command"]
                }
            }
        }

    def _create_completion(self, messages: List[Dict]) -> Any:
        return self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=[self.kubectl_tool_definition],
            tool_choice="auto"
        )

    def _handle_tool_response(self, response: Any) -> Tuple[bool, List[Dict], str]:
        response_message = response.choices[0].message
        
        if response_message.tool_calls:
            new_messages = []
            for tool_call in response_message.tool_calls:
                if tool_call.function.name == "run_kubectl":
                    func_args = json.loads(tool_call.function.arguments)
                    stdout, stderr, return_code = self._execute_kubectl(func_args["command"])
                    
                    new_messages.extend([
                        {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [tool_call]
                        },
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": stdout if return_code == 0 else f"Error: {stderr}"
                        }
                    ])
            return True, new_messages, ""
        return False, [], response_message.content
