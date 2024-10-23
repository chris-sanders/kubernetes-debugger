from .openai import OpenAIHandler
#from .anthropic import AnthropicHandler

def get_llm_handler(provider: str, model: str, config: dict):
    if provider == "openai":
        return OpenAIHandler(model=model, api_key=config["api_keys"]["openai"])
    elif provider == "anthropic":
        return AnthropicHandler(model=model, api_key=config["api_keys"]["anthropic"])
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
