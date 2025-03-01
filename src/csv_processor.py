"""
File: csv_processor.py
Directory: /content/drive/MyDrive/Colab Notebooks/automated_reporting/src/

This script processes CSV files from the raw data directory,
detects date formats, and converts them to a standardized format
for data analysis and Plotly visualizations. It also generates
a rich visualization configuration file.
"""

import os
import pandas as pd
import json
import re
from pathlib import Path
import random
import colorsys
import logging
from datetime import datetime

# Import the ProjectPaths class
from path_config import ProjectPaths

def setup_logging():
    """Setup logging configuration"""
    paths = ProjectPaths()
    log_dir = paths.logs_dir
    
    # Create logs directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    log_file = os.path.join(log_dir, 'pipeline.log')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

def generate_distinct_colors(n):
    """Generate n visually distinct colors"""
    colors = []
    for i in range(n):
        hue = i / n
        saturation = 0.7 + random.uniform(-0.2, 0.2)  # Slight variation in saturation
        value = 0.9 + random.uniform(-0.2, 0.1)  # Slight variation in value
        
        # Convert HSV to RGB
        r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
        
        # Convert to hex
        color = f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'
        colors.append(color)
    
    return colors

def process_csv_files():
    """Process all CSV files in the raw data directory"""
    # Setup logging
    logger = setup_logging()
    
    # Initialize paths
    paths = ProjectPaths()
    raw_data_path = paths.raw_data_dir
    processed_data_path = paths.processed_data_dir
    dictionary_path = paths.dictionary_dir

    # Log start of processing
    logger.info("Processing all files in raw directory")

    # Function to determine date type
    def determine_date_type(date_col):
        """Determine if dates are yearly, quarterly, or monthly"""
        # Check some sample values to determine format
        sample = date_col.iloc[0] if not date_col.empty else ""
        
        if re.match(r'^\d{4}$', str(sample)):
            return "yearly"
        elif re.match(r'^\d{4}-Q[1-4]$', str(sample)):
            return "quarterly"
        elif re.match(r'^\d{4}-\d{2}$', str(sample)):
            return "monthly"
        else:
            # If unable to determine, check more samples
            for date in date_col.iloc[1:min(10, len(date_col))]:
                if re.match(r'^\d{4}$', str(date)):
                    return "yearly"
                elif re.match(r'^\d{4}-Q[1-4]$', str(date)):
                    return "quarterly"
                elif re.match(r'^\d{4}-\d{2}$', str(date)):
                    return "monthly"
            
            # If still unclear, make a best guess based on structure
            return "unknown"

    # Find all CSV files in the raw data directory
    csv_files = [f for f in os.listdir(raw_data_path) if f.endswith('.csv')]
    excel_files = [f for f in os.listdir(raw_data_path) if f.endswith(('.xlsx', '.xls'))]
    
    all_files = csv_files + excel_files
    logger.info(f"Found {len(all_files)} data files in {raw_data_path}")

    # Load existing file descriptions if available
    file_descriptions_path = paths.file_descriptions_path
    if os.path.exists(file_descriptions_path):
        try:
            with open(file_descriptions_path, 'r') as f:
                file_descriptions = json.load(f)
        except:
            file_descriptions = {}
    else:
        file_descriptions = {}

    # Process each file
    for file in all_files:
        file_path = os.path.join(raw_data_path, file)
        logger.info(f"Step 1: Converting {file} to standardized format")
        
        try:
            # Read the file
            if file.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
                # Create a CSV version
                csv_file = os.path.splitext(file)[0] + '.csv'
                csv_path = os.path.join(raw_data_path, csv_file)
                df.to_csv(csv_path, index=False)
                file = csv_file  # Update file name for further processing
            else:
                df = pd.read_csv(file_path)
            
            # Convert first column to string if it's not already
            first_col_name = df.columns[0]
            df[first_col_name] = df[first_col_name].astype(str)
            
            # Get file basename
            basename = os.path.splitext(file)[0]
            
            # Step 2: Validation
            logger.info(f"Step 2: Validating {basename}")
            
            # Basic validation checks
            validation_issues = False
            
            # Check for missing values
            if df.isna().any().any():
                validation_issues = True
                logger.warning(f"Missing values found in {file}")
            
            # Check for proper numeric data in all columns except first
            for col in df.columns[1:]:
                if not pd.api.types.is_numeric_dtype(df[col]):
                    try:
                        # Try to convert to numeric
                        df[col] = pd.to_numeric(df[col])
                    except:
                        validation_issues = True
                        logger.warning(f"Column {col} in {file} contains non-numeric data")
            
            if validation_issues:
                logger.warning(f"Validation issues with {basename}. Proceeding with caution.")
            
            # Step 3: Cleaning and preparing data
            logger.info(f"Step 3: Cleaning and preparing {basename}")
            
            # Determine date type
            date_type = determine_date_type(df[first_col_name])
            
            # Process dataframe according to date type for analysis
            if date_type == "yearly":
                # Convert to datetime year
                df[first_col_name] = pd.to_datetime(df[first_col_name], format='%Y').dt.to_period('Y')
            elif date_type == "quarterly":
                # Convert to PeriodIndex for quarters
                df[first_col_name] = pd.PeriodIndex(df[first_col_name], freq='Q')
            elif date_type == "monthly":
                # Convert to datetime for months
                df[first_col_name] = pd.to_datetime(df[first_col_name]).dt.to_period('M')
            
            variable_names = df.columns[1:].tolist()
            num_variables = len(variable_names)
            
            # Generate distinct colors for each variable
            colors = generate_distinct_colors(num_variables)
            
            # Create default visualization configs
            if basename not in file_descriptions:
                # Default y-axis suffix based on file name - customize as needed
                y_suffix = ""
                if "uitgaven" in basename.lower() or "kosten" in basename.lower():
                    y_suffix = "(EUR)"
                elif "aantal" in basename.lower():
                    y_suffix = "(Count)"
                
                # Create default individual graph configs for each variable
                variable_graphs = {}
                for i, var_name in enumerate(variable_names):
                    # Format the variable name for display (convert snake_case to Title Case)
                    display_name = " ".join(word.capitalize() for word in var_name.split('_'))
                    
                    # Create default graph config for this variable
                    variable_graphs[var_name] = {
                        "display_name": display_name,
                        "description": f"Data for {display_name}",
                        "color": colors[i],
                        "visible": True,
                        "graph_id": f"{basename}_{var_name}",  # Default unique graph ID
                        "graph_config": {
                            "title": f"{display_name} Over Time",
                            "type": "line",  # Default graph type
                            "x_axis": {
                                "title": "Time Period",
                                "format": "auto"  # Let Plotly decide based on data
                            },
                            "y_axis": {
                                "title": f"Value {y_suffix}",
                                "format": ",.1f"  # Default number format
                            }
                        }
                    }
                
                # Create a combined view that shows all variables on one graph
                combined_graph_config = {
                    "id": f"{basename}_combined",
                    "title": f"{' '.join(word.capitalize() for word in basename.split('_'))} - All Variables",
                    "type": "line",
                    "variables": variable_names,
                    "x_axis": {
                        "title": "Time Period",
                        "format": "auto"
                    },
                    "y_axis": {
                        "title": f"Value {y_suffix}",
                        "format": ",.1f"
                    }
                }
                
                # Create basic file description
                file_descriptions[basename] = {
                    "number_of_variables": num_variables,
                    "variable_names": variable_names,
                    "date_type": date_type,
                    "number_of_data_points": len(df),
                    "visualization": {
                        "variables": variable_graphs,
                        "graph_groups": [
                            {
                                "id": "individual",
                                "description": "Individual graphs for each variable",
                                "graphs": [f"{basename}_{var}" for var in variable_names]
                            },
                            {
                                "id": "combined",
                                "description": "All variables on a single graph",
                                "graphs": [f"{basename}_combined"]
                            }
                        ],
                        "combined_graphs": [combined_graph_config]
                    }
                }
            
            # Save processed dataframe
            processed_file_path = os.path.join(processed_data_path, file)
            df.to_csv(processed_file_path, index=False)
            
            # Also save as pickle for easy loading in Python
            pickle_path = os.path.join(processed_data_path, f"{basename}.pkl")
            df.to_pickle(pickle_path)
            
            logger.info(f"Successfully processed {file} through all pipeline steps")
            
        except Exception as e:
            logger.error(f"Error processing {file}: {str(e)}")

    # Save all file descriptions to a single JSON file
    with open(paths.file_descriptions_path, 'w') as f:
        json.dump(file_descriptions, f, indent=4)

    # Count successful files
    successful_files = len(file_descriptions)
    logger.info(f"Processing summary: {successful_files}/{len(all_files)} files successfully processed")

    return file_descriptions

if __name__ == "__main__":
    process_csv_files()