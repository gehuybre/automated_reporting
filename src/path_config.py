"""
File: path_config.py
Directory: /content/drive/MyDrive/Colab Notebooks/automated_reporting/src/

This module defines the file and directory paths used across the project,
using a centralized configuration file.
"""

import os
import json
from pathlib import Path
import datetime

class ProjectPaths:
    """Class that handles project paths configuration"""
    
    def __init__(self, config_path=None):
        """
        Initialize paths from the configuration file
        
        Parameters:
        config_path (str): Path to the configuration file
                          If None, uses the default location
        """
        # Default configuration path
        if config_path is None:
            config_path = "/content/drive/MyDrive/Colab Notebooks/automated_reporting/data/dictionaries/paths_config.json"
        
        self.config_path = config_path
        self._load_config()
        
    def _load_config(self):
        """Load paths from the configuration file"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                
            # Set all paths from config
            for key, path in config.items():
                setattr(self, key, path)
                
            # Create additional path attributes
            self._create_additional_paths()
            
        except FileNotFoundError:
            print(f"Configuration file not found at {self.config_path}")
            # Set default paths
            self._set_default_paths()
            
        except json.JSONDecodeError:
            print(f"Error parsing JSON configuration at {self.config_path}")
            # Set default paths
            self._set_default_paths()
    
    def _set_default_paths(self):
        """Set default paths if config file is not available"""
        base_path = "/content/drive/MyDrive/Colab Notebooks/automated_reporting"
        
        # Main directories
        self.base_path = base_path
        self.src_dir = os.path.join(base_path, "src")
        self.data_dir = os.path.join(base_path, "data")
        self.raw_data_dir = os.path.join(base_path, "data", "raw")
        self.processed_data_dir = os.path.join(base_path, "data", "processed")
        self.dictionary_dir = os.path.join(base_path, "data", "dictionaries")
        self.logs_dir = os.path.join(base_path, "data", "logs")
        self.output_dir = os.path.join(base_path, "output")
        self.reports_dir = os.path.join(base_path, "output", "reports")
        self.visualizations_dir = os.path.join(base_path, "output", "visualizations")
        self.html_reports_dir = os.path.join(base_path, "output", "html_reports")
        self.templates_dir = os.path.join(base_path, "templates")
        self.css_dir = os.path.join(base_path, "templates", "css")
        self.js_dir = os.path.join(base_path, "templates", "js")
        self.config_dir = os.path.join(base_path, "config")
        
        # Configuration files
        self.file_descriptions_path = os.path.join(self.dictionary_dir, "file_descriptions.json")
        self.paths_config_path = os.path.join(self.dictionary_dir, "paths_config.json")
        self.plotly_layout_config_path = os.path.join(self.dictionary_dir, "plotly_layout_config.json")
        self.dashboard_config_path = os.path.join(self.config_dir, "dashboard_config.json")
        self.report_config_path = os.path.join(self.config_dir, "report_config.json")
        
        # Source files
        self.html_report_preview_path = os.path.join(self.src_dir, "html_report_preview.py")
        self.generate_html_report_path = os.path.join(self.src_dir, "generate_html_report.py")
        
        # Logs
        self.pipeline_log_path = os.path.join(self.logs_dir, "pipeline.log")
        
        # Create additional path attributes
        self._create_additional_paths()
    
    def _create_additional_paths(self):
        """Create additional paths that depend on the base paths"""
        # Create a timestamped directory for current visualizations
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_visualizations_dir = os.path.join(self.visualizations_dir, timestamp)
        
        # Add paths for tables
        self.tables_dir = os.path.join(self.output_dir, "tables")
    
    def create_directories(self):
        """Create all directories in the path configuration if they don't exist"""
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
            self.html_reports_dir,
            self.current_visualizations_dir,
            self.templates_dir,
            self.css_dir,
            self.js_dir,
            self.config_dir,
            self.tables_dir
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def save_config(self, path=None):
        """
        Save current configuration to a JSON file
        
        Parameters:
        path (str): Path to save the configuration
                   If None, uses the paths_config_path
        """
        if path is None:
            path = self.paths_config_path
        
        # Create dictionary of paths
        config = {}
        for key, value in self.__dict__.items():
            # Skip private attributes and the config_path itself
            if not key.startswith('_') and key != 'config_path':
                config[key] = value
        
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Save the configuration
        with open(path, 'w') as f:
            json.dump(config, f, indent=4)
        
        print(f"Configuration saved to {path}")


if __name__ == "__main__":
    # Create paths object
    paths = ProjectPaths()
    
    # Create all directories
    paths.create_directories()
    
    # Print paths for verification
    for key, value in paths.__dict__.items():
        if not key.startswith('_') and key != 'config_path':
            print(f"{key}: {value}")