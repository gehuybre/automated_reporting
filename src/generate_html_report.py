"""
File: generate_html_report.py
Directory: /content/drive/MyDrive/Colab Notebooks/automated_reporting/src/

Main script to generate HTML reports with tables and visualizations.
This orchestrates the entire process from data analysis to report generation.
"""

import os
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path

# Import project modules
from path_config import ProjectPaths
from data_analysis_utils import DataAnalyzer
from html_table_generator import HTMLTableGenerator
from html_report_preview import HTMLReportPreview

def setup_logging():
    """Setup logging configuration"""
    paths = ProjectPaths()
    log_dir = paths.logs_dir
    
    # Create logs directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f'report_generation_{timestamp}.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

def generate_html_report(dataset_name=None, theme="default", include_yoy=True, include_analysis=True):
    """
    Generate an HTML report for a dataset or all datasets
    
    Parameters:
    dataset_name (str): Name of the dataset, or None for all datasets
    theme (str): Visualization theme to use
    include_yoy (bool): Whether to include year-over-year changes
    include_analysis (bool): Whether to include data analysis
    
    Returns:
    list: Paths to generated report files
    """
    logger = setup_logging()
    logger.info("Starting HTML report generation")
    
    # Initialize paths
    paths = ProjectPaths()
    
    # Create required directories
    tables_dir = os.path.join(paths.output_dir, "tables")
    os.makedirs(tables_dir, exist_ok=True)
    os.makedirs(paths.reports_dir, exist_ok=True)
    os.makedirs(paths.html_reports_dir, exist_ok=True)
    
    # Load file descriptions
    try:
        with open(paths.file_descriptions_path, 'r') as f:
            file_descriptions = json.load(f)
        logger.info(f"Loaded {len(file_descriptions)} dataset descriptions")
    except Exception as e:
        logger.error(f"Error loading file descriptions: {str(e)}")
        return []
    
    # Determine which datasets to process
    if dataset_name:
        if dataset_name in file_descriptions:
            datasets_to_process = [dataset_name]
        else:
            logger.error(f"Dataset {dataset_name} not found in file descriptions")
            return []
    else:
        datasets_to_process = list(file_descriptions.keys())
    
    logger.info(f"Will process {len(datasets_to_process)} datasets")
    
    # Initialize components
    data_analyzer = DataAnalyzer()
    table_generator = HTMLTableGenerator()
    report_generator = HTMLReportPreview(theme=theme)
    
    # Generate reports
    generated_reports = []
    
    for dataset in datasets_to_process:
        logger.info(f"Processing dataset: {dataset}")
        
        # Step 1: Analyze data (if requested)
        if include_analysis:
            logger.info(f"Running data analysis for {dataset}")
            try:
                # Calculate YoY changes
                _, yoy_df = data_analyzer.calculate_yoy_changes(dataset)
                
                # Calculate summary statistics
                summary = data_analyzer.calculate_summary_statistics(dataset)
                
                # Generate insights
                insights = data_analyzer.generate_insights(dataset)
                
                logger.info(f"Completed data analysis for {dataset}")
            except Exception as e:
                logger.error(f"Error in data analysis for {dataset}: {str(e)}")
                # Continue with report generation even if analysis fails
        
        # Step 2: Generate HTML tables
        logger.info(f"Generating HTML table for {dataset}")
        try:
            table_html = table_generator.generate_data_table_html(
                dataset_name=dataset,
                include_yoy=include_yoy
            )
            
            # Save table HTML to file
            table_path = os.path.join(tables_dir, f"{dataset}_table.html")
            with open(table_path, 'w', encoding='utf-8') as f:
                f.write(table_html)
            
            logger.info(f"Saved HTML table to {table_path}")
        except Exception as e:
            logger.error(f"Error generating HTML table for {dataset}: {str(e)}")
            # Continue with report generation even if table generation fails
        
        # Step 3: Generate report preview
        logger.info(f"Generating report preview for {dataset}")
        try:
            report_path = report_generator.generate_report_preview(
                dataset_name=dataset,
                include_yoy=include_yoy,
                include_viz=True
            )
            
            if report_path:
                generated_reports.append(report_path)
                logger.info(f"Generated report preview: {report_path}")
            else:
                logger.warning(f"No report preview generated for {dataset}")
        except Exception as e:
            logger.error(f"Error generating report preview for {dataset}: {str(e)}")
    
    # Summary
    logger.info(f"Report generation complete. Generated {len(generated_reports)} reports.")
    for report in generated_reports:
        logger.info(f"- {report}")
    
    return generated_reports

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate HTML reports for datasets')
    parser.add_argument('--dataset', type=str, help='Specific dataset to process')
    parser.add_argument('--theme', type=str, default='default', help='Visualization theme')
    parser.add_argument('--no-yoy', action='store_true', help='Disable year-over-year calculations')
    parser.add_argument('--no-analysis', action='store_true', help='Disable data analysis')
    
    args = parser.parse_args()
    
    # Generate reports
    reports = generate_html_report(
        dataset_name=args.dataset,
        theme=args.theme,
        include_yoy=not args.no_yoy,
        include_analysis=not args.no_analysis
    )
    
    print(f"Generated {len(reports)} reports:")
    for report in reports:
        print(f"- {report}")