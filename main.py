# main.py
import yaml
from typing import Optional
import logging
from llm_handlers import get_llm_handler

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def main():
    config = load_config()
    llm_handler = get_llm_handler(
        config['llm_provider'], 
        config['model'],
        config
    )
    
    while True:
        user_input = input("\nDescribe the issue (or type 'exit' to quit): ")
        if user_input.lower() == 'exit':
            break
            
        try:
            response = llm_handler.process_query(user_input)
            print("\nResponse:", response)
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            print(f"\nError: {e}")

if __name__ == "__main__":
    main()
