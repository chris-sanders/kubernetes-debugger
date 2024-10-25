#!/bin/bash

# If first argument is "config", handle configuration
if [ "$1" = "config" ]; then
    echo "Configuration mode - to be implemented"
    exit 0
fi

# Default behavior: run the main application
exec python main.py "$@"
