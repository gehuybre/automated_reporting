"""
File: setup_project.py
Directory: /content/drive/MyDrive/Colab Notebooks/automated_reporting/

This script initializes the project structure and copies source files
to the appropriate locations.
"""

import os
import shutil
from pathlib import Path
import sys

def setup_project():
    """
    Set up the project structure and copy source files to their locations.
    """
    # Define base path
    base_path = "/content/drive/MyDrive/Colab Notebooks/automated_reporting"
    
    # Define source and target paths
    src_dir = os.path.join(base_path, "src")
    
    # Create the src directory if it doesn't exist
    Path(src_dir).mkdir(parents=True, exist_ok=True)
    
    # Create __init__.py file in src directory
    init_path = os.path.join(src_dir, "__init__.py")
    with open(init_path, 'w') as f:
        f.write("""\"\"\"
Automated Reporting Package

This package contains utilities for processing and visualizing time series data.
\"\"\"
""")
    print(f"Created {init_path}")
    
    # No need to copy files if they're already in the src directory
    print("\nChecking for source files...")
    source_files = ["path_config.py", "csv_processor.py"]
    for file in source_files:
        file_path = os.path.join(src_dir, file)
        if os.path.exists(file_path):
            print(f"✓ {file} already exists in {src_dir}")
        else:
            print(f"✗ {file} not found in {src_dir}")
    
    # Add src directory to Python path for imports
    if src_dir not in sys.path:
        sys.path.append(src_dir)
        print(f"Added {src_dir} to Python path")
    
    print("\nProject setup complete. The following directory structure has been created:")
    print(f"{base_path}/")
    print(f"├── src/")
    print(f"│   ├── __init__.py")
    print(f"│   ├── path_config.py  (if exists)")
    print(f"│   └── csv_processor.py  (if exists)")
    print(f"├── data/")
    print(f"│   ├── raw/")
    print(f"│   ├── processed/")
    print(f"│   └── dictionaries/")
    print(f"└── output/")
    print(f"    ├── reports/")
    print(f"    └── visualizations/")
    
    print("\nProject setup complete. The following directory structure has been created:")
    print(f"{base_path}/")
    print(f"├── src/")
    print(f"│   ├── __init__.py")
    print(f"│   ├── path_config.py")
    print(f"│   └── csv_processor.py")
    print(f"├── data/")
    print(f"│   ├── raw/")
    print(f"│   ├── processed/")
    print(f"│   └── dictionaries/")
    print(f"└── output/")
    print(f"    ├── reports/")
    print(f"    └── visualizations/")

if __name__ == "__main__":
    setup_project()