"""
File: data_statistics.py
Directory: /content/drive/MyDrive/Colab Notebooks/automated_reporting/src/

This script calculates various statistics from data files, including:
- Year-over-year percentage changes
- 5-year averages
- Quarterly comparisons with previous year (for quarterly data)
- Minimum and maximum values with their occurrence dates
The results are saved as a JSON file for later use in LLM prompts.
"""

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime

# Import project modules
from path_config import ProjectPaths

def setup_logging():
    """Setup logging configuration"""
    paths = ProjectPaths()
    log_dir = paths.logs_dir
    
    # Create logs directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    log_file = os.path.join(log_dir, 'statistics.log')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

def calculate_dataset_statistics(dataset_name=None):
    """
    Calculate statistics for specified dataset or all available datasets
    
    Parameters:
    dataset_name (str): Name of dataset to process, or None for all
    
    Returns:
    dict: Dictionary containing calculated statistics
    """
    # Setup logging
    logger = setup_logging()
    
    # Initialize paths
    paths = ProjectPaths()
    
    # Load file descriptions
    with open(paths.file_descriptions_path, 'r') as f:
        file_descriptions = json.load(f)
    
    # Determine datasets to process
    if dataset_name:
        if dataset_name in file_descriptions:
            datasets_to_process = [dataset_name]
        else:
            logger.error(f"Dataset '{dataset_name}' not found")
            return None
    else:
        datasets_to_process = list(file_descriptions.keys())
    
    if not datasets_to_process:
        logger.error("No datasets found to process")
        return None
    
    # Dictionary to store all statistics
    all_statistics = {}
    
    # Process each dataset
    for dataset_name in datasets_to_process:
        logger.info(f"Processing statistics for dataset: {dataset_name}")
        
        # Load dataset configuration
        dataset_config = file_descriptions[dataset_name]
        date_type = dataset_config.get('date_type', 'yearly')
        
        # Load the dataset
        data_path_csv = os.path.join(paths.processed_data_dir, f"{dataset_name}.csv")
        raw_data_path = os.path.join(paths.raw_data_dir, f"{dataset_name}.csv")
        
        if os.path.exists(data_path_csv):
            df = pd.read_csv(data_path_csv)
        elif os.path.exists(raw_data_path):
            df = pd.read_csv(raw_data_path)
        else:
            logger.error(f"Could not find data file for dataset: {dataset_name}")
            continue
        
        # Get date column and variable columns
        date_column = df.columns[0]
        variable_columns = df.columns[1:].tolist()
        
        # Convert date column to proper datetime format
        try:
            # First, try to parse as generic datetime without forcing format
            df[date_column] = pd.to_datetime(df[date_column])
            
            # Then, extract the date components we need based on date_type
            if date_type == 'yearly':
                # For yearly data, we only need the year
                df['year'] = df[date_column].dt.year
            elif date_type == 'quarterly':
                # For quarterly data, we need year and quarter
                df['year'] = df[date_column].dt.year
                df['quarter'] = df[date_column].dt.quarter
            elif date_type == 'monthly':
                # For monthly data, we need year and month
                df['year'] = df[date_column].dt.year
                df['month'] = df[date_column].dt.month
        except Exception as e:
            logger.error(f"Error parsing dates: {str(e)}")
            logger.info("Attempting alternative date parsing methods...")
            
            # Try different parsing methods
            if date_type == 'yearly':
                # Extract just the year if it's in 'YYYY-MM-DD' format
                if df[date_column].str.contains('-').any():
                    df['year'] = df[date_column].str.split('-').str[0].astype(int)
                else:
                    df['year'] = df[date_column].astype(int)
            elif date_type == 'quarterly':
                # Handle 'YYYY-QN' format
                if df[date_column].str.contains('Q').any():
                    df['year'] = df[date_column].str.split('Q').str[0].astype(int)
                    df['quarter'] = df[date_column].str.split('Q').str[1].astype(int)
                else:
                    # Try to extract quarter from date in 'YYYY-MM-DD' format
                    df[date_column] = pd.to_datetime(df[date_column])
                    df['year'] = df[date_column].dt.year
                    df['quarter'] = df[date_column].dt.quarter
            elif date_type in ['monthly', 'unknown']:
                # Handle 'YYYY-MM' or 'YYYY-MM-DD' format
                df[date_column] = pd.to_datetime(df[date_column])
                df['year'] = df[date_column].dt.year
                df['month'] = df[date_column].dt.month
        
        # Sort by date to ensure chronological order
        df = df.sort_values(by=date_column)
        
        # Dictionary to store statistics for this dataset
        dataset_statistics = {
            "dataset_name": dataset_name,
            "date_type": date_type,
            "statistics_generated_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "variables": {}
        }
        
        # Process each variable
        for variable in variable_columns:
            logger.info(f"Calculating statistics for variable: {variable}")
            
            # Get variable display name from configuration
            display_name = variable
            if ('visualization' in dataset_config and 
                'variables' in dataset_config['visualization'] and
                variable in dataset_config['visualization']['variables']):
                display_name = dataset_config['visualization']['variables'][variable].get('display_name', variable)
            
            # Dictionary to store statistics for this variable
            variable_stats = {
                "name": variable,
                "display_name": display_name,
                "year_over_year_changes": {},
                "five_year_averages": {},
                "quarterly_comparisons": {} if date_type == 'quarterly' else None,
                "minimum": {"value": None, "date": None},
                "maximum": {"value": None, "date": None}
            }
            
            # Extract data series for this variable
            series = df[variable]
            
            # Calculate year-over-year percentage changes
            if date_type == 'yearly':
                # For yearly data, directly calculate YoY changes
                yoy_changes = series.pct_change() * 100
                
                # Store YoY changes with years as keys
                for i, (date, value) in enumerate(zip(df[date_column], yoy_changes)):
                    if i > 0:  # Skip the first row (no previous year to compare)
                        year_str = date.strftime('%Y')
                        variable_stats["year_over_year_changes"][year_str] = round(value, 2)
            
            elif date_type == 'quarterly':
                # For quarterly data, compare with same quarter of previous year
                # Check if we already have year and quarter columns
                if 'quarter' not in df.columns or 'year' not in df.columns:
                    # Extract year and quarter from date if not already available
                    try:
                        df['year'] = df[date_column].dt.year
                        df['quarter'] = df[date_column].dt.quarter
                    except:
                        # Attempt to extract from string format like '2015-Q1'
                        if df[date_column].dtype == 'object' and df[date_column].str.contains('Q').any():
                            df['year'] = df[date_column].str.split('Q').str[0].astype(int)
                            df['quarter'] = df[date_column].str.split('Q').str[1].astype(int)
                
                # Group by quarter and calculate YoY changes
                try:
                    for quarter in df['quarter'].unique():
                        quarter_data = df[df['quarter'] == quarter].sort_values(by='year')
                        quarterly_series = quarter_data[variable]
                        
                        # Calculate percentage changes
                        quarterly_changes = quarterly_series.pct_change() * 100
                        
                        # Store quarterly comparisons
                        for i, (year, value) in enumerate(zip(quarter_data['year'], quarterly_changes)):
                            if i > 0 and not pd.isna(value):  # Skip the first year and NaN values
                                period_key = f"{year}-Q{quarter}"
                                variable_stats["quarterly_comparisons"][period_key] = round(value, 2)
                except Exception as e:
                    logger.warning(f"Error calculating quarterly changes: {str(e)}")
                    variable_stats["quarterly_comparisons"] = {"error": f"Could not calculate: {str(e)}"}
                
                # Also calculate yearly changes for quarterly data
                yearly_avg = df.groupby('year')[variable].mean()
                yoy_changes = yearly_avg.pct_change() * 100
                
                # Store YoY changes with years as keys
                for year, value in zip(yearly_avg.index, yoy_changes):
                    if not pd.isna(value):  # Skip the first year (no previous year to compare)
                        variable_stats["year_over_year_changes"][str(year)] = round(value, 2)
            
            elif date_type == 'monthly':
                # For monthly data, compare with same month of previous year
                # Check if we already have year and month columns
                if 'month' not in df.columns or 'year' not in df.columns:
                    # Extract year and month from date if not already available
                    try:
                        df['year'] = df[date_column].dt.year
                        df['month'] = df[date_column].dt.month
                    except:
                        logger.warning(f"Could not extract month and year from date column")
                
                # Group by month and calculate YoY changes
                try:
                    monthly_changes = {}
                    for month in df['month'].unique():
                        month_data = df[df['month'] == month].sort_values(by='year')
                        if len(month_data) > 1:  # Need at least 2 years for comparison
                            monthly_series = month_data[variable]
                            monthly_pct_change = monthly_series.pct_change() * 100
                            
                            for i, (year, value) in enumerate(zip(month_data['year'][1:], monthly_pct_change[1:])):
                                if not pd.isna(value):  # Skip NaN values
                                    period_key = f"{year}-{month:02d}"
                                    monthly_changes[period_key] = round(value, 2)
                except Exception as e:
                    logger.warning(f"Error calculating monthly changes: {str(e)}")
                    monthly_changes = {"error": f"Could not calculate: {str(e)}"}
                
                # Also calculate yearly changes for monthly data
                yearly_avg = df.groupby('year')[variable].mean()
                yoy_changes = yearly_avg.pct_change() * 100
                
                # Store YoY changes with years as keys
                for year, value in zip(yearly_avg.index, yoy_changes):
                    if not pd.isna(value):  # Skip the first year (no previous year to compare)
                        variable_stats["year_over_year_changes"][str(year)] = round(value, 2)
            
            # Calculate 5-year averages (rolling window)
            try:
                if len(df) >= 5:
                    # Group by year
                    if 'year' in df.columns:
                        yearly_data = df.groupby('year')[variable].mean()
                    else:
                        # If we don't have a 'year' column, try to create one from date_column
                        if pd.api.types.is_datetime64_any_dtype(df[date_column]):
                            yearly_data = df.groupby(df[date_column].dt.year)[variable].mean()
                        else:
                            # For string dates like "2015-01-01", extract the year
                            years = [int(str(d).split('-')[0]) for d in df[date_column]]
                            yearly_data = pd.Series(df[variable].values, index=years).groupby(level=0).mean()
                    
                    # Calculate 5-year rolling average
                    rolling_avg = yearly_data.rolling(window=5).mean()
                    
                    # Store the 5-year averages
                    for i, (year, avg) in enumerate(rolling_avg.items()):
                        if i >= 4:  # Need at least 5 years of data for 5-year average
                            if not pd.isna(avg):
                                variable_stats["five_year_averages"][str(year)] = round(avg, 2)
            except Exception as e:
                logger.warning(f"Error calculating 5-year averages: {str(e)}")
                variable_stats["five_year_averages"] = {"error": f"Could not calculate: {str(e)}"}
            
            # Find minimum and maximum values
            try:
                min_idx = series.idxmin()
                max_idx = series.idxmax()
                
                # Format dates based on date_type
                if date_type == 'yearly':
                    if 'year' in df.columns:
                        min_date_str = str(df.loc[min_idx, 'year'])
                        max_date_str = str(df.loc[max_idx, 'year'])
                    else:
                        # Try to extract year from the date column
                        min_date = df.loc[min_idx, date_column]
                        max_date = df.loc[max_idx, date_column]
                        
                        if pd.api.types.is_datetime64_any_dtype(df[date_column]):
                            min_date_str = min_date.strftime('%Y')
                            max_date_str = max_date.strftime('%Y')
                        else:
                            # For string dates like "2015-01-01", extract the year
                            min_date_str = str(min_date).split('-')[0]
                            max_date_str = str(max_date).split('-')[0]
                
                elif date_type == 'quarterly':
                    if 'year' in df.columns and 'quarter' in df.columns:
                        min_year = df.loc[min_idx, 'year']
                        min_quarter = df.loc[min_idx, 'quarter']
                        min_date_str = f"{min_year}-Q{min_quarter}"
                        
                        max_year = df.loc[max_idx, 'year']
                        max_quarter = df.loc[max_idx, 'quarter']
                        max_date_str = f"{max_year}-Q{max_quarter}"
                    else:
                        # Try to parse from date column
                        min_date = df.loc[min_idx, date_column]
                        max_date = df.loc[max_idx, date_column]
                        
                        if pd.api.types.is_datetime64_any_dtype(df[date_column]):
                            min_quarter = pd.Timestamp(min_date).quarter
                            min_date_str = f"{pd.Timestamp(min_date).strftime('%Y')}-Q{min_quarter}"
                            
                            max_quarter = pd.Timestamp(max_date).quarter
                            max_date_str = f"{pd.Timestamp(max_date).strftime('%Y')}-Q{max_quarter}"
                        else:
                            # For string dates, just use as is
                            min_date_str = str(min_date)
                            max_date_str = str(max_date)
                
                else:  # monthly or unknown
                    if 'year' in df.columns and 'month' in df.columns:
                        min_year = df.loc[min_idx, 'year']
                        min_month = df.loc[min_idx, 'month']
                        min_date_str = f"{min_year}-{min_month:02d}"
                        
                        max_year = df.loc[max_idx, 'year']
                        max_month = df.loc[max_idx, 'month']
                        max_date_str = f"{max_year}-{max_month:02d}"
                    else:
                        # Try to parse from date column
                        min_date = df.loc[min_idx, date_column]
                        max_date = df.loc[max_idx, date_column]
                        
                        if pd.api.types.is_datetime64_any_dtype(df[date_column]):
                            min_date_str = pd.Timestamp(min_date).strftime('%Y-%m')
                            max_date_str = pd.Timestamp(max_date).strftime('%Y-%m')
                        else:
                            # For string dates, just use the first 7 characters (YYYY-MM)
                            min_date_str = str(min_date)[:7] if len(str(min_date)) >= 7 else str(min_date)
                            max_date_str = str(max_date)[:7] if len(str(max_date)) >= 7 else str(max_date)
            except Exception as e:
                logger.warning(f"Error determining min/max dates: {str(e)}")
                min_date_str = "unknown"
                max_date_str = "unknown"
            
            # Store min/max values
            variable_stats["minimum"]["value"] = round(series.min(), 2)
            variable_stats["minimum"]["date"] = min_date_str
            
            variable_stats["maximum"]["value"] = round(series.max(), 2)
            variable_stats["maximum"]["date"] = max_date_str
            
            # Add statistics for this variable to the dataset statistics
            dataset_statistics["variables"][variable] = variable_stats
        
        # Add statistics for this dataset to the overall statistics
        all_statistics[dataset_name] = dataset_statistics
    
    # Create statistics directory if it doesn't exist
    stats_dir = os.path.join(paths.data_dir, 'statistics')
    os.makedirs(stats_dir, exist_ok=True)
    
    # Save statistics to JSON file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(stats_dir, f"statistics_{timestamp}.json")
    
    with open(output_file, 'w') as f:
        json.dump(all_statistics, f, indent=4)
    
    logger.info(f"Statistics saved to {output_file}")
    
    return all_statistics

def format_statistics_for_prompt(statistics):
    """
    Format the statistics into a text form suitable for an LLM prompt
    
    Parameters:
    statistics (dict): The statistics dictionary
    
    Returns:
    str: Formatted text suitable for a prompt
    """
    # Setup logging
    logger = setup_logging()
    prompt_text = []
    
    for dataset_name, dataset_stats in statistics.items():
        # Format dataset header
        dataset_header = f"Dataset: {dataset_name}"
        prompt_text.append(dataset_header)
        prompt_text.append("=" * len(dataset_header))
        prompt_text.append(f"Date Type: {dataset_stats['date_type']}")
        prompt_text.append(f"Generated on: {dataset_stats['statistics_generated_on']}")
        prompt_text.append("")
        
        # Format each variable's statistics
        for var_name, var_stats in dataset_stats['variables'].items():
            var_display = var_stats['display_name']
            prompt_text.append(f"Variable: {var_display} ({var_name})")
            prompt_text.append("-" * len(f"Variable: {var_display} ({var_name})"))
            
            # Minimum and maximum
            prompt_text.append(f"Minimum: {var_stats['minimum']['value']} (occurred in {var_stats['minimum']['date']})")
            prompt_text.append(f"Maximum: {var_stats['maximum']['value']} (occurred in {var_stats['maximum']['date']})")
            
            # Year-over-year changes
            prompt_text.append("\nYear-over-year percentage changes:")
            for year, change in var_stats['year_over_year_changes'].items():
                prompt_text.append(f"  {year}: {change:.2f}%")
            
            # 5-year averages
            if var_stats['five_year_averages']:
                prompt_text.append("\n5-year rolling averages:")
                for year, avg in var_stats['five_year_averages'].items():
                    prompt_text.append(f"  {year}: {avg:.2f}")
            
            # Quarterly comparisons (if applicable)
            if var_stats['quarterly_comparisons']:
                prompt_text.append("\nQuarterly year-over-year percentage changes:")
                for quarter, change in var_stats['quarterly_comparisons'].items():
                    prompt_text.append(f"  {quarter}: {change:.2f}%")
            
            prompt_text.append("\n")
        
        prompt_text.append("\n" + "-"*50 + "\n")
    
    # Create text for prompt
    paths = ProjectPaths()
    stats_dir = os.path.join(paths.data_dir, 'statistics')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(stats_dir, f"statistics_prompt_{timestamp}.txt")
    
    # Write to file
    with open(output_file, 'w') as f:
        f.write("\n".join(prompt_text))
    
    logger.info(f"Statistics prompt text saved to {output_file}")
    
    return "\n".join(prompt_text)

if __name__ == "__main__":
    # Calculate statistics for all datasets
    statistics = calculate_dataset_statistics()
    
    # Format statistics for an LLM prompt
    if statistics:
        prompt_text = format_statistics_for_prompt(statistics)
        print("Statistics calculated and formatted for LLM prompt. Check the output files.")