import logging
from typing import Optional
import yaml
from rich.console import Console
from rich.markdown import Markdown
from llm_handlers import get_llm_handler

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create a console instance
console = Console()

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
        console.print("\nDescribe the issue (or type 'exit' to quit, 'reset' for new conversation): ", style="bold blue")
        user_input = input()
        
        if user_input.lower() == 'exit':
            break
        elif user_input.lower() == 'reset':
            llm_handler.reset_conversation()
            console.print("\nConversation reset.", style="bold yellow")
            continue
        elif user_input.lower() == 'history':
            history = llm_handler.get_conversation_history()
            console.print("\nConversation History:", style="bold magenta")
            for msg in history:
                role_color = "cyan" if msg["role"] == "user" else "green"
                console.print(f"\n[bold {role_color}]{msg['role']}:[/bold {role_color}] {msg['content']}")
            continue
            
        try:
            response = llm_handler.process_query(user_input)
            console.print("\nResponse:", style="bold green")
            # Convert the response to a Markdown object and print it
            md = Markdown(response)
            console.print(md)
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            console.print(f"\nError: {e}", style="bold red")

if __name__ == "__main__":
    main()
