# llm_handlers/openai.py
from typing import List, Dict, Any
import json
import logging
from openai import OpenAI
from .base import BaseLLMHandler
from kubectl_handler import execute_kubectl_command

logger = logging.getLogger(__name__)

class OpenAIHandler(BaseLLMHandler):
    def __init__(self, model: str, api_key: str):
        super().__init__(model)
        self.client = OpenAI(api_key=api_key)
        # Define the function that OpenAI can call
        self.functions = [
            {
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
        ]
        
    def process_query(self, query: str) -> str:
        messages = [
            {"role": "system", "content": """You are a Kubernetes cluster debugging assistant. 
            You have read-only access to the cluster through kubectl commands.
            Analyze issues and provide clear explanations.
            When you need information, use kubectl commands through the provided function."""},
            {"role": "user", "content": query}
        ]

        while True:
            logger.info("Sending request to OpenAI...")
            logger.debug(f"Messages: {messages}")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.functions,  # Use self.functions here
                tool_choice="auto"
            )
            
            response_message = response.choices[0].message
            
            # If the model wants to call a function
            if response_message.tool_calls:
                for tool_call in response_message.tool_calls:
                    if tool_call.function.name == "run_kubectl":
                        # Parse the function arguments
                        func_args = json.loads(tool_call.function.arguments)
                        kubectl_command = func_args["command"]
                        logger.info(f"Model requested kubectl command: {kubectl_command}")
                        
                        # Execute kubectl command
                        stdout, stderr, return_code = execute_kubectl_command(kubectl_command)
                        
                        # Add the function call and result to the message history
                        messages.append({
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [tool_call]
                        })
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": stdout if return_code == 0 else f"Error: {stderr}"
                        })
            else:
                logger.info("Model provided final response")
                return response_message.content
