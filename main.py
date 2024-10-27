# main.py
import logging
import yaml
import threading
from rich.console import Console

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('kubernetes-debugger')
console = Console()

# Global variables for dependency loading
dependencies_loaded = threading.Event()
llm_handler = None
markdown_module = None

def load_dependencies(config):
    """Load heavy dependencies in background"""
    global llm_handler, markdown_module
    try:
        from rich.markdown import Markdown
        from llm_handlers import get_llm_handler
        
        markdown_module = Markdown
        llm_handler = get_llm_handler(
            config['llm_provider'],
            config['model'],
            config
        )
        dependencies_loaded.set()
    except Exception as e:
        logger.error(f"Error loading dependencies: {e}")
        dependencies_loaded.set()

def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def get_multiline_input() -> str:
    """Collect all input lines until double empty line or EOF"""
    console.print("(Enter input, press Enter twice when done)", style="bold cyan")
    lines = []
    empty_line_count = 0
    
    try:
        first_line = input()
        if first_line.lower() in ['exit', 'reset']:
            return first_line
            
        lines.append(first_line)
        
        while True:
            try:
                line = input()
                if not line:
                    empty_line_count += 1
                    if empty_line_count >= 2:
                        console.print("Processing input...", style="bold yellow")
                        break
                else:
                    empty_line_count = 0
                    lines.append(line)
            except EOFError:
                break
            
        final_input = '\n'.join(lines).strip()
        return final_input
        
    except EOFError:
        return ""

def main():
    config = load_config()
    if config.get('debug', False):
        logger.setLevel(logging.DEBUG)

    # Start loading dependencies in background
    loading_thread = threading.Thread(target=load_dependencies, args=(config,))
    loading_thread.daemon = True
    loading_thread.start()

    while True:
        console.print("\nDescribe the issue (or type 'exit' to quit, 'reset' for new conversation): ", style="bold blue")
        user_input = get_multiline_input()
        
        if not user_input:
            continue
            
        if user_input.lower() == 'exit':
            break
            
        # Wait for dependencies to be loaded before processing
        if not dependencies_loaded.is_set():
            console.print("Finalizing initialization...", style="bold yellow")
            dependencies_loaded.wait()
            
        if user_input.lower() == 'reset':
            llm_handler.reset_conversation()
            console.print("\nConversation reset.", style="bold yellow")
            continue
            
        try:
            response = llm_handler.process_query(user_input)
            console.print("\nResponse:", style="bold green")
            md = markdown_module(response)
            console.print(md)
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            console.print(f"\nError: {e}", style="bold red")

if __name__ == "__main__":
    main()
