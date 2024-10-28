# Kubernetes AI Debugger

An experimental tool for exploring LLM tool calling capabilities with kubectl. This project allows an LLM to explore and analyze your Kubernetes cluster through natural language interaction.

⚠️ **Warning**: While the LLM is instructed to perform read-only operations, there are currently no technical controls enforcing this limitation. **Do not use this tool with production clusters.**

## Running the Tool

## Configuration

Copy the example configuration file and add your API keys:
```bash
cp config.yaml.example config.yaml
```

Edit `config.yaml` to add your:
- OpenAI API key
- Anthropic API key (optional)
- Preferred model settings

The configuration file must be accessible to the application, either:
- In the current directory when running locally
- Mounted to the container when running via Docker


### Using Docker (Recommended)

Pull and run the latest development build:
```bash
docker run -it \
  -v $KUBECONFIG:/root/.kube/config \
  -v $(pwd)/config.yaml:/app/config.yaml \
  ghcr.io/chris-sanders/kubernetes-debugger:dev
```

### Local Development

Requirements:
- Python 3.12
- Poetry

```bash
# Clone the repository
git clone https://github.com/chris-sanders/kubernetes-debugger.git
cd kubernetes-debugger

# Install dependencies
poetry install

# Run the application
poetry shell
python main.py
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
