"""
File: debug_data_loading.py
Directory: /content/drive/MyDrive/Colab Notebooks/automated_reporting/src/

This script helps debug data loading issues with the visualization pipeline.
It verifies data file existence and column names to fix the "Variable not found" warnings.
"""

import os
import pandas as pd
import json
from pathlib import Path

def debug_data_loading(base_path="/content/drive/MyDrive/Colab Notebooks/automated_reporting"):
    """
    Debug data loading issues with the automated reporting system.
    
    This function:
    1. Checks if data files exist in the expected locations
    2. Validates column names against file_descriptions.json
    3. Identifies case sensitivity issues
    4. Suggests fixes for the visualization system
    """
    print("===== Automated Reporting System Debug =====")
    
    # Define paths
    data_dir = os.path.join(base_path, "data")
    raw_data_dir = os.path.join(data_dir, "raw")
    processed_data_dir = os.path.join(data_dir, "processed")
    dictionary_dir = os.path.join(data_dir, "dictionaries")
    file_descriptions_path = os.path.join(dictionary_dir, "file_descriptions.json")
    
    # Check if directories exist
    print("\n== Checking Directory Structure ==")
    directories = [data_dir, raw_data_dir, processed_data_dir, dictionary_dir]
    for directory in directories:
        exists = os.path.isdir(directory)
        print(f"{directory}: {'EXISTS' if exists else 'MISSING'}")
    
    # Load file descriptions
    print("\n== Checking File Descriptions ==")
    if os.path.exists(file_descriptions_path):
        with open(file_descriptions_path, 'r') as f:
            try:
                file_descriptions = json.load(f)
                print(f"Successfully loaded {file_descriptions_path}")
                dataset_names = list(file_descriptions.keys())
                print(f"Datasets defined: {dataset_names}")
            except json.JSONDecodeError:
                print(f"ERROR: {file_descriptions_path} is not valid JSON")
                return
    else:
        print(f"ERROR: {file_descriptions_path} does not exist")
        return
    
    # Check CSV files
    print("\n== Checking Data Files ==")
    for dataset_name in dataset_names:
        # Check raw file
        raw_csv_path = os.path.join(raw_data_dir, f"{dataset_name}.csv")
        raw_xlsx_path = os.path.join(raw_data_dir, f"{dataset_name}.xlsx")
        
        # Check processed file
        processed_csv_path = os.path.join(processed_data_dir, f"{dataset_name}.csv")
        processed_pkl_path = os.path.join(processed_data_dir, f"{dataset_name}.pkl")
        
        print(f"\nDataset: {dataset_name}")
        print(f"Raw CSV: {'EXISTS' if os.path.exists(raw_csv_path) else 'MISSING'}")
        print(f"Raw XLSX: {'EXISTS' if os.path.exists(raw_xlsx_path) else 'MISSING'}")
        print(f"Processed CSV: {'EXISTS' if os.path.exists(processed_csv_path) else 'MISSING'}")
        print(f"Processed PKL: {'EXISTS' if os.path.exists(processed_pkl_path) else 'MISSING'}")
        
        # If data file exists, check columns
        data_path = None
        df = None
        
        if os.path.exists(processed_csv_path):
            data_path = processed_csv_path
        elif os.path.exists(raw_csv_path):
            data_path = raw_csv_path
        
        if data_path:
            try:
                df = pd.read_csv(data_path)
                print(f"Successfully loaded data from {data_path}")
                print(f"Columns in data file: {list(df.columns)}")
                
                # Check against file_descriptions
                expected_variables = file_descriptions[dataset_name].get('variable_names', [])
                print(f"Variables in file_descriptions: {expected_variables}")
                
                # Check for missing columns
                missing_vars = [var for var in expected_variables if var not in df.columns]
                if missing_vars:
                    print(f"WARNING: Missing variables: {missing_vars}")
                    
                    # Check for case sensitivity issues
                    lowercase_columns = {col.lower(): col for col in df.columns}
                    case_issues = []
                    
                    for var in missing_vars:
                        if var.lower() in lowercase_columns:
                            actual_col = lowercase_columns[var.lower()]
                            case_issues.append((var, actual_col))
                    
                    if case_issues:
                        print("\nCase sensitivity issues detected:")
                        for expected, actual in case_issues:
                            print(f"  Expected: '{expected}', Actual: '{actual}'")
                        
                        print("\nSuggested solutions:")
                        print("1. Update file_descriptions.json to match actual column names")
                        print("2. Use case-insensitive column matching in visualization_utils.py")
                    else:
                        print("\nColumns are truly missing from the dataset")
                else:
                    print("All expected variables found in the dataset")
            except Exception as e:
                print(f"ERROR loading data from {data_path}: {str(e)}")
        else:
            print("No data file found to check columns")
    
    print("\n== Summary of Issues ==")
    print("1. Check for case sensitivity issues between file_descriptions.json and actual data files")
    print("2. Ensure data files are properly loaded in correct order (pkl > csv)")
    print("3. Update visualization_utils.py to handle case-insensitive column matching")
    
    print("\n===== Debug Complete =====")

if __name__ == "__main__":
    debug_data_loading()