#!/bin/bash

# If first argument is "config", handle configuration
if [ "$1" = "config" ]; then
    # Handle config setup
    echo "Configuration mode - to be implemented"
    exit 0
fi

# Default behavior: run the main application
exec python main.py "$@"
