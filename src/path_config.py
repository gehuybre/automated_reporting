"""
File: path_config.py
Directory: /content/drive/MyDrive/Colab Notebooks/automated_reporting/src/

This module defines the project path structure and provides utilities
for accessing standardized file paths across the project.
"""

import json
import os
from pathlib import Path
import datetime

class ProjectPaths:
    def __init__(self, base_path="/content/drive/MyDrive/Colab Notebooks/automated_reporting"):
        """Initialize project paths with a configurable base path"""
        self.base_path = base_path
        
        # Source code directory
        self.src_dir = os.path.join(base_path, "src")
        
        # Main data directories
        self.data_dir = os.path.join(base_path, "data")
        self.raw_data_dir = os.path.join(self.data_dir, "raw")
        self.processed_data_dir = os.path.join(self.data_dir, "processed")
        self.dictionary_dir = os.path.join(self.data_dir, "dictionaries")
        self.logs_dir = os.path.join(self.data_dir, "logs")
        
        # Output directories for reports and visualizations
        self.output_dir = os.path.join(base_path, "output")
        self.reports_dir = os.path.join(self.output_dir, "reports")
        self.visualizations_dir = os.path.join(self.output_dir, "visualizations")
        
        # Dynamic visualization directory with timestamp
        current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_visualizations_dir = os.path.join(self.visualizations_dir, current_time)
        
        # Metadata file paths
        self.file_descriptions_path = os.path.join(self.dictionary_dir, "file_descriptions.json")
        self.paths_config_path = os.path.join(self.dictionary_dir, "paths_config.json")
        self.plotly_layout_config_path = os.path.join(self.dictionary_dir, "plotly_layout_config.json")
        
        # Pipeline log path
        self.pipeline_log_path = os.path.join(self.logs_dir, "pipeline.log")
        
        # Create all directories
        self._create_directories()
        
        # Save the paths to a JSON file
        self.save_paths_to_json()
    
    def _create_directories(self):
        """Create all necessary directories if they don't exist"""
        directories = [
            self.src_dir,
            self.data_dir,
            self.raw_data_dir,
            self.processed_data_dir, 
            self.dictionary_dir,
            self.logs_dir,
            self.output_dir,
            self.reports_dir,
            self.visualizations_dir,
            self.current_visualizations_dir
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            
    def get_dataset_visualization_dir(self, dataset_name):
        """Get visualization directory for a specific dataset"""
        return os.path.join(self.current_visualizations_dir, dataset_name)
    
    def get_paths_dict(self):
        """Return a dictionary containing all paths"""
        return {
            "base_path": self.base_path,
            "src_dir": self.src_dir,
            "data_dir": self.data_dir,
            "raw_data_dir": self.raw_data_dir,
            "processed_data_dir": self.processed_data_dir,
            "dictionary_dir": self.dictionary_dir,
            "logs_dir": self.logs_dir,
            "output_dir": self.output_dir,
            "reports_dir": self.reports_dir,
            "visualizations_dir": self.visualizations_dir,
            "current_visualizations_dir": self.current_visualizations_dir,
            "file_descriptions_path": self.file_descriptions_path,
            "paths_config_path": self.paths_config_path,
            "plotly_layout_config_path": self.plotly_layout_config_path,
            "pipeline_log_path": self.pipeline_log_path
        }
    
    def save_paths_to_json(self):
        """Save all paths to a JSON config file"""
        with open(self.paths_config_path, 'w') as f:
            json.dump(self.get_paths_dict(), f, indent=4)
        print(f"Paths configuration saved to {self.paths_config_path}")
    
    @classmethod
    def load_from_json(cls, json_path=None):
        """Load paths from a JSON file"""
        if json_path is None:
            # Try to find paths_config.json in standard locations
            base_paths = [
                "/content/drive/MyDrive/Colab Notebooks/automated_reporting",
                os.getcwd()
            ]
            
            for base in base_paths:
                possible_path = os.path.join(base, "data", "dictionaries", "paths_config.json")
                if os.path.exists(possible_path):
                    json_path = possible_path
                    break
            
            if json_path is None:
                raise FileNotFoundError("Could not find paths_config.json")
        
        with open(json_path, 'r') as f:
            paths_dict = json.load(f)
        
        # Create a new instance using the base path from the config
        instance = cls(base_path=paths_dict.get("base_path"))
        return instance


if __name__ == "__main__":
    # Create and save project paths
    paths = ProjectPaths()
    
    # Print out all paths
    for name, path in paths.get_paths_dict().items():
        print(f"{name}: {path}")