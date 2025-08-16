#!/bin/bash

# Setup script for pre-commit hooks
echo "Setting up pre-commit hooks..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Install pre-commit if not already installed
if ! command -v pre-commit &> /dev/null; then
    echo "Installing pre-commit..."
    pip install pre-commit==3.6.0
else
    echo "pre-commit is already installed"
fi

# Install the pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install

# Run pre-commit on all files to ensure everything is formatted
echo "Running pre-commit on all files..."
pre-commit run --all-files

echo "Pre-commit setup complete!"
echo ""
echo "The following hooks are now active:"
echo "- Black code formatting"
echo "- MyPy type checking"
echo "- Django tests (on commit)"
echo ""
echo "To run hooks manually: pre-commit run --all-files"
echo "To run a specific hook: pre-commit run black"
echo "To run type checking: make typecheck"
