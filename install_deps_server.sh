#!/bin/bash
# Install dependencies on ECO server

echo "Installing Python dependencies..."

# Check if conda is available
if command -v conda &> /dev/null; then
    echo "Using conda environment..."
    conda install -y numpy pandas psycopg2 sqlalchemy
else
    echo "Using pip..."
    pip install --user numpy pandas psycopg2-binary sqlalchemy
fi

echo ""
echo "✓ Dependencies installed!"
echo ""
echo "Verifying installation..."
python -c "import numpy; import pandas; import psycopg2; import sqlalchemy; print('✓ All packages imported successfully!')"
