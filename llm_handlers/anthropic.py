# llm_handlers/anthropic.py
from typing import List, Dict, Any, Tuple
import logging
from anthropic import Anthropic
from .base import BaseLLMHandler

logger = logging.getLogger(__name__)

class AnthropicHandler(BaseLLMHandler):
    def _initialize_client(self):
        return Anthropic(api_key=self.api_key)

    def _get_kubectl_tool_definition(self) -> Dict:
        return {
            "name": "run_kubectl",
            "description": "Run a kubectl command to inspect the kubernetes cluster",
            "input_schema": {
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

    def _initialize_messages(self, query: str) -> List[Dict]:
        """Anthropic only needs the user message in the messages list"""
        return [
            {"role": "user", "content": query}
        ]

    def _create_completion(self, messages: List[Dict]) -> Any:
        return self.client.messages.create(
            model=self.model,
            system=self.system_prompt,
            messages=messages,
            tools=[self.kubectl_tool_definition],
            max_tokens=1500
        )

    def _handle_tool_response(self, response: Any) -> Tuple[bool, List[Dict], str]:
        # Extract tool use blocks from the response
        tool_use_blocks = [
            block for block in response.content 
            if block.type == "tool_use"
        ]
        
        if tool_use_blocks:
            new_messages = []
            for block in tool_use_blocks:
                # Execute the kubectl command
                kubectl_command = block.input["command"]
                stdout, stderr, return_code = self._execute_kubectl(kubectl_command)
                
                # Add the result back to messages
                new_messages.extend([
                    {
                        "role": "assistant",
                        "content": [
                            {
                                "type": "tool_use",
                                "id": block.id,
                                "name": "run_kubectl",
                                "input": {"command": kubectl_command}
                            }
                        ]
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": stdout if return_code == 0 else f"Error: {stderr}"
                            }
                        ]
                    }
                ])
            return True, new_messages, ""
        else:
            # If no tool use, return the text response
            text_blocks = [
                block for block in response.content 
                if block.type == "text"
            ]
            if text_blocks:
                return False, [], text_blocks[0].text
            return False, [], "No response text found"
