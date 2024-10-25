import logging
from typing import Optional
import yaml
from rich.console import Console
from rich.markdown import Markdown
from llm_handlers import get_llm_handler

logger = logging.getLogger(__name__)

# Configure the root logger to WARNING (or any other level you prefer)
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create a console instance
console = Console()

def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def get_multiline_input() -> str:
    """Collect all input lines until double empty line or EOF"""
    console.print("(Enter input, press Enter twice when done)", style="bold cyan")
    lines = []
    empty_line_count = 0
    
    try:
        # Handle single-word commands immediately
        first_line = input()
        if first_line.lower() in ['exit', 'reset']:
            return first_line
            
        lines.append(first_line)
        
        while True:
            try:
                line = input()
                if not line:
                    empty_line_count += 1
                    if empty_line_count >= 2:  # Two consecutive empty lines means we're done
                        console.print("Processing input...", style="bold yellow")
                        break
                else:
                    empty_line_count = 0
                    lines.append(line)
            except EOFError:  # Handle EOF (ctrl+d)
                break
            
        final_input = '\n'.join(lines).strip()
        return final_input
        
    except EOFError:  # Handle EOF at the very first input
        return ""

def main():
    config = load_config()
    
    # Configure logging based on the 'debug' flag in the config
    if config.get('debug', False):
        logging.getLogger('kubernetes-debugger').setLevel(logging.DEBUG)
    else:
        logging.getLogger('kubernetes-debugger').setLevel(logging.WARNING)
    
    llm_handler = get_llm_handler(
        config['llm_provider'],
        config['model'],
        config
    )

    while True:
        console.print("\nDescribe the issue (or type 'exit' to quit, 'reset' for new conversation): ", style="bold blue")
        user_input = get_multiline_input()
        
        if not user_input:  # Skip empty inputs
            continue
            
        if user_input.lower() == 'exit':
            break
        elif user_input.lower() == 'reset':
            llm_handler.reset_conversation()
            console.print("\nConversation reset.", style="bold yellow")
            continue
            
        try:
            response = llm_handler.process_query(user_input)
            console.print("\nResponse:", style="bold green")
            md = Markdown(response)
            console.print(md)
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            console.print(f"\nError: {e}", style="bold red")

if __name__ == "__main__":
    main()
