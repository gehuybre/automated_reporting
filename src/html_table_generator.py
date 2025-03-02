"""
File: html_table_generator.py
Directory: /content/drive/MyDrive/Colab Notebooks/automated_reporting/src/

This script generates HTML tables from the processed data,
including calculations for year-over-year (YoY) changes.
These tables can be used in HTML reports with Jinja.
"""

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime

# Import project modules - modify imports as needed
from path_config import ProjectPaths

def setup_logging():
    """Setup logging configuration"""
    paths = ProjectPaths()
    log_dir = paths.logs_dir
    
    # Create logs directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    log_file = os.path.join(log_dir, 'html_tables.log')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

class HTMLTableGenerator:
    """Class to generate HTML tables from data with YoY calculations"""
    
    def __init__(self, custom_css=None):
        """
        Initialize the table generator
        
        Parameters:
        custom_css (str): Optional custom CSS to include in the table
        """
        self.logger = setup_logging()
        self.paths = ProjectPaths()
        
        # Create output directories if they don't exist
        self.tables_dir = os.path.join(self.paths.output_dir, "tables")
        os.makedirs(self.tables_dir, exist_ok=True)
        
        # Load file descriptions
        try:
            with open(self.paths.file_descriptions_path, 'r') as f:
                self.file_descriptions = json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading file descriptions: {str(e)}")
            self.file_descriptions = {}
        
        # Default CSS styles
        self.default_css = """
        <style>
            .data-table {
                width: 100%;
                border-collapse: collapse;
                font-family: Arial, sans-serif;
                margin-bottom: 20px;
            }
            .data-table th, .data-table td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: right;
            }
            .data-table th {
                background-color: #f2f2f2;
                text-align: center;
                font-weight: bold;
            }
            .data-table tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            .data-table tr:hover {
                background-color: #f0f0f0;
            }
            .data-table .date-column {
                text-align: left;
                font-weight: bold;
            }
            .positive-change {
                color: green;
            }
            .negative-change {
                color: red;
            }
            .region-header {
                font-weight: bold;
                background-color: #e9e9e9;
            }
            .yoy-row {
                font-style: italic;
                background-color: #f5f5f5;
            }
            caption {
                caption-side: top;
                font-weight: bold;
                text-align: center;
                padding: 10px;
                font-size: 1.2em;
            }
        </style>
        """
        
        # Use custom CSS if provided
        self.css = custom_css if custom_css else self.default_css
    
    def _format_value(self, value, format_str="{:,.0f}"):
        """Format a numeric value according to specified format"""
        if pd.isna(value):
            return "-"
        return format_str.format(value)
    
    def _format_percent(self, value, format_str="{:+.1f}%"):
        """Format a percentage value with + or - sign"""
        if pd.isna(value):
            return "-"
        return format_str.format(value)
    
    def _calculate_yoy_changes(self, df):
        """
        Calculate year-over-year percentage changes for all numeric columns
        
        Parameters:
        df (DataFrame): DataFrame with a date column and numeric data columns
        
        Returns:
        DataFrame: DataFrame with YoY changes
        """
        # Make a copy to avoid modifying the original
        df_copy = df.copy()
        
        # Ensure the date column is properly formatted
        date_col = df_copy.columns[0]
        
        # Convert to datetime if not already
        if not pd.api.types.is_datetime64_dtype(df_copy[date_col]):
            try:
                df_copy[date_col] = pd.to_datetime(df_copy[date_col])
            except:
                # If conversion fails, proceed anyway
                self.logger.warning(f"Could not convert {date_col} to datetime")
        
        # Extract year from date
        try:
            df_copy['year'] = df_copy[date_col].dt.year
        except:
            # If extraction fails, try to extract year directly from string
            try:
                df_copy['year'] = df_copy[date_col].str.extract(r'(\d{4})').astype(int)
            except:
                self.logger.error(f"Could not extract year from {date_col}")
                return None
        
        # Calculate YoY changes for each numeric column
        yoy_df = pd.DataFrame()
        yoy_df[date_col] = df_copy[date_col]
        yoy_df['year'] = df_copy['year']
        
        # For each numeric column, calculate the percentage change
        for col in df_copy.columns:
            if col not in [date_col, 'year'] and pd.api.types.is_numeric_dtype(df_copy[col]):
                # Calculate pct_change with a period of 1 year
                # Group by year first to handle cases where there might be multiple records per year
                grouped = df_copy.groupby('year')[col].mean()
                pct_change = grouped.pct_change() * 100  # Convert to percentage
                
                # Map the percentage changes back to the original dates
                year_to_pct = pct_change.to_dict()
                yoy_df[f'{col}_yoy'] = yoy_df['year'].map(year_to_pct)
        
        return yoy_df
    
    def generate_data_table_html(self, dataset_name, title=None, include_yoy=True):
        """
        Generate an HTML table for a dataset with optional YoY changes
        
        Parameters:
        dataset_name (str): Name of the dataset
        title (str): Table title/caption (optional)
        include_yoy (bool): Whether to include YoY calculations
        
        Returns:
        str: HTML table content
        """
        # Set default title if not provided
        if not title:
            title = f"{' '.join(word.capitalize() for word in dataset_name.split('_'))}"
        
        # Load the dataset
        try:
            # Try to load from processed data first
            data_path = os.path.join(self.paths.processed_data_dir, f"{dataset_name}.csv")
            df = pd.read_csv(data_path)
            
            # If the file exists but is empty, try raw data
            if df.empty:
                raise pd.errors.EmptyDataError("Processed file is empty")
                
        except (FileNotFoundError, pd.errors.EmptyDataError):
            # Try loading from raw data
            try:
                data_path = os.path.join(self.paths.raw_data_dir, f"{dataset_name}.csv")
                df = pd.read_csv(data_path)
            except (FileNotFoundError, pd.errors.EmptyDataError) as e:
                self.logger.error(f"Could not load dataset {dataset_name}: {str(e)}")
                return f"<p>Error: Could not load dataset {dataset_name}</p>"
        
        # Get dataset configuration
        dataset_config = self.file_descriptions.get(dataset_name, {})
        
        # Get variable display names and formatting
        display_names = {}
        formats = {}
        
        # Ensure first column is handled properly (usually date)
        date_col = df.columns[0]
        display_names[date_col] = "Date"
        
        # Process column metadata from file_descriptions.json
        if 'visualization' in dataset_config and 'variables' in dataset_config['visualization']:
            for var_name, var_config in dataset_config['visualization']['variables'].items():
                # Find the matching column in the dataframe (case-insensitive)
                matching_cols = [col for col in df.columns if col.lower() == var_name.lower()]
                
                if matching_cols:
                    col_name = matching_cols[0]
                    display_names[col_name] = var_config.get('display_name', col_name)
                    
                    # Get number format from graph_config if available
                    if 'graph_config' in var_config and 'y_axis' in var_config['graph_config']:
                        y_format = var_config['graph_config']['y_axis'].get('format')
                        if y_format:
                            formats[col_name] = y_format
        
        # Fill in any missing display names with capitalized column names
        for col in df.columns:
            if col not in display_names:
                display_names[col] = " ".join(word.capitalize() for word in col.split('_'))
        
        # Calculate YoY changes if requested
        yoy_df = None
        if include_yoy:
            yoy_df = self._calculate_yoy_changes(df)
        
        # Begin HTML table
        html = []
        html.append(self.css)
        html.append('<div class="table-container">')
        html.append(f'<table class="data-table" id="table-{dataset_name}">')
        
        # Add caption/title
        html.append(f'<caption>{title}</caption>')
        
        # Header row
        html.append('<thead>')
        html.append('<tr>')
        html.append(f'<th class="date-column">{display_names[date_col]}</th>')
        
        # Add header for each data column
        for col in df.columns[1:]:
            html.append(f'<th>{display_names.get(col, col)}</th>')
        
        html.append('</tr>')
        html.append('</thead>')
        
        # Table body
        html.append('<tbody>')
        
        # Iterate through rows
        for i, row in df.iterrows():
            html.append('<tr class="data-row">')
            
            # Date column
            date_val = row[date_col]
            html.append(f'<td class="date-column">{date_val}</td>')
            
            # Data columns
            for col in df.columns[1:]:
                value = row[col]
                
                # Format the value
                if pd.api.types.is_numeric_dtype(df[col]):
                    format_str = "{:,.0f}" if col not in formats else formats[col]
                    formatted_value = self._format_value(value, format_str)
                else:
                    formatted_value = value
                
                html.append(f'<td>{formatted_value}</td>')
            
            html.append('</tr>')
            
            # Add YoY change row if available
            if include_yoy and yoy_df is not None:
                # Find matching row in YoY DataFrame
                yoy_rows = yoy_df[yoy_df[date_col] == row[date_col]]
                
                if not yoy_rows.empty:
                    yoy_row = yoy_rows.iloc[0]
                    
                    # Only add YoY row if we have at least one non-null YoY value
                    has_yoy_values = False
                    for col in df.columns[1:]:
                        yoy_col = f'{col}_yoy'
                        if yoy_col in yoy_row and not pd.isna(yoy_row[yoy_col]):
                            has_yoy_values = True
                            break
                    
                    if has_yoy_values:
                        html.append('<tr class="yoy-row">')
                        html.append('<td class="date-column">YoY Change</td>')
                        
                        for col in df.columns[1:]:
                            yoy_col = f'{col}_yoy'
                            
                            if yoy_col in yoy_row:
                                yoy_value = yoy_row[yoy_col]
                                
                                if pd.isna(yoy_value):
                                    html.append('<td>-</td>')
                                else:
                                    # Format with + or - sign and color code
                                    css_class = "positive-change" if yoy_value >= 0 else "negative-change"
                                    formatted_yoy = self._format_percent(yoy_value)
                                    html.append(f'<td class="{css_class}">{formatted_yoy}</td>')
                            else:
                                html.append('<td>-</td>')
                        
                        html.append('</tr>')
            
        html.append('</tbody>')
        html.append('</table>')
        html.append('</div>')
        
        return '\n'.join(html)
    
    def generate_all_tables(self, output_dir=None, include_yoy=True):
        """
        Generate HTML tables for all datasets in file_descriptions
        
        Parameters:
        output_dir (str): Directory to save tables (default is tables_dir)
        include_yoy (bool): Whether to include YoY calculations
        
        Returns:
        dict: Dictionary of {dataset_name: html_content}
        """
        if output_dir is None:
            output_dir = self.tables_dir
        
        os.makedirs(output_dir, exist_ok=True)
        
        tables = {}
        for dataset_name in self.file_descriptions.keys():
            self.logger.info(f"Generating table for dataset: {dataset_name}")
            
            try:
                # Generate the HTML table
                title = " ".join(word.capitalize() for word in dataset_name.split('_'))
                html_content = self.generate_data_table_html(
                    dataset_name=dataset_name,
                    title=title,
                    include_yoy=include_yoy
                )
                
                # Save to file
                output_path = os.path.join(output_dir, f"{dataset_name}_table.html")
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(html_content)
                
                self.logger.info(f"Saved table to {output_path}")
                tables[dataset_name] = html_content
                
            except Exception as e:
                self.logger.error(f"Error generating table for {dataset_name}: {str(e)}")
        
        return tables

    def preview_table(self, dataset_name, include_yoy=True):
        """
        Generate and display a preview of the HTML table for a dataset
        
        Parameters:
        dataset_name (str): Name of the dataset
        include_yoy (bool): Whether to include YoY calculations
        
        Returns:
        str: HTML table content (for display in Jupyter notebook or similar)
        """
        title = " ".join(word.capitalize() for word in dataset_name.split('_'))
        html_content = self.generate_data_table_html(
            dataset_name=dataset_name,
            title=title,
            include_yoy=include_yoy
        )
        
        return html_content


if __name__ == "__main__":
    # Create table generator
    table_generator = HTMLTableGenerator()
    
    # Preview an individual table
    html_content = table_generator.preview_table("bbc_investeringsuitgaven_wegen_infra")
    print("Table HTML preview (first 500 chars):", html_content[:500])
    
    # Generate all tables
    tables = table_generator.generate_all_tables()
    print(f"Generated {len(tables)} HTML tables")