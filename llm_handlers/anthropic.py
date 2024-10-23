# llm_handlers/anthropic.py
from typing import List, Dict, Any
import json
import logging
from anthropic import Anthropic
from .base import BaseLLMHandler
from kubectl_handler import execute_kubectl_command

logger = logging.getLogger(__name__)

class AnthropicHandler(BaseLLMHandler):
    def __init__(self, model: str, api_key: str):
        super().__init__(model)
        self.client = Anthropic(api_key=api_key)
        self.tools = [{
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
        }]

    def process_query(self, query: str) -> str:
        messages = [
            {
                "role": "user",
                "content": query
            }
        ]

        while True:
            logger.info("Sending request to Anthropic...")
            
            response = self.client.messages.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
                max_tokens=1500
            )
            
            # Check if any content block is a tool_use
            tool_use_blocks = [
                block for block in response.content 
                if block.type == "tool_use"
            ]
            
            if tool_use_blocks:
                for block in tool_use_blocks:
                    # Execute the kubectl command
                    kubectl_command = block.input["command"]
                    logger.info(f"Model requested kubectl command: {kubectl_command}")
                    
                    stdout, stderr, return_code = execute_kubectl_command(kubectl_command)
                    
                    # Add the result back to messages
                    messages.append({
                        "role": "assistant",
                        "content": [
                            {
                                "type": "tool_use",
                                "id": block.id,
                                "name": "run_kubectl",
                                "input": {"command": kubectl_command}
                            }
                        ]
                    })
                    messages.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": stdout if return_code == 0 else f"Error: {stderr}"
                            }
                        ]
                    })
            else:
                # If no tool use, return the text response
                logger.info("Model provided final response")
                text_blocks = [
                    block for block in response.content 
                    if block.type == "text"
                ]
                if text_blocks:
                    return text_blocks[0].text
                return "No response text found"
