"""
File: generate_visualizations.py
Directory: /content/drive/MyDrive/Colab Notebooks/automated_reporting/src/

This script generates visualizations from processed data files
using the configuration defined in file_descriptions.json.
"""

import os
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import logging
from pathlib import Path
from datetime import datetime

# Import project modules
from path_config import ProjectPaths
from visualization_utils import VisualizationManager

def setup_logging():
    """Setup logging configuration"""
    paths = ProjectPaths()
    log_dir = paths.logs_dir
    
    # Create logs directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    log_file = os.path.join(log_dir, 'visualization.log')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

def generate_visualizations(datasets=None, theme="default", save_format="png"):
    """
    Generate visualizations for specified datasets or all available datasets
    
    Parameters:
    datasets (list): List of dataset names to process, or None for all
    theme (str): The Plotly theme to use
    save_format (str): Format to save visualizations (png, svg, pdf, etc.)
    """
    # Setup logging
    logger = setup_logging()
    
    # Initialize paths
    paths = ProjectPaths()
    
    # Initialize visualization manager
    viz_manager = VisualizationManager(theme=theme)
    
    # Load file descriptions
    with open(paths.file_descriptions_path, 'r') as f:
        file_descriptions = json.load(f)
    
    # If no specific datasets provided, use all
    if datasets is None:
        datasets = list(file_descriptions.keys())
    
    # Filter to only include datasets that exist in file_descriptions
    valid_datasets = [d for d in datasets if d in file_descriptions]
    if len(valid_datasets) < len(datasets):
        logger.warning(f"Some specified datasets not found: {set(datasets) - set(valid_datasets)}")
    
    if not valid_datasets:
        logger.error("No valid datasets found to visualize")
        return
    
    # Create visualizations directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    viz_dir = os.path.join(paths.visualizations_dir, timestamp)
    os.makedirs(viz_dir, exist_ok=True)
    
    # Process each dataset
    for dataset_name in valid_datasets:
        logger.info(f"Processing visualizations for dataset: {dataset_name}")
        
        dataset_config = file_descriptions[dataset_name]
        visualization_config = dataset_config.get('visualization', {})
        
        # Get graph groups
        graph_groups = visualization_config.get('graph_groups', [])
        
        # Create directory for this dataset
        dataset_dir = os.path.join(viz_dir, dataset_name)
        os.makedirs(dataset_dir, exist_ok=True)
        
        # Generate individual graphs
        variables = visualization_config.get('variables', {})
        for var_name, var_config in variables.items():
            if var_config.get('visible', True):  # Only generate for visible variables
                graph_id = var_config.get('graph_id')
                display_name = var_config.get('display_name', var_name)
                
                logger.info(f"Generating individual graph: {var_config['graph_config']['title']} ({graph_id})")
                
                try:
                    # Create the visualization
                    fig = viz_manager.create_visualization(
                        dataset_name=dataset_name,
                        variable_names=[var_name],
                        graph_id=graph_id
                    )
                    
                    # Save the visualization
                    filename = f"{graph_id}.{save_format}"
                    filepath = os.path.join(dataset_dir, filename)
                    fig.write_image(filepath)
                    
                    logger.info(f"Saved {display_name} visualization to {filepath}")
                except Exception as e:
                    logger.error(f"Error creating visualization for {display_name}: {str(e)}")
        
        # Generate combined graphs
        combined_graphs = visualization_config.get('combined_graphs', [])
        for graph_config in combined_graphs:
            graph_id = graph_config.get('id')
            title = graph_config.get('title', f"{dataset_name} Combined")
            
            logger.info(f"Generating combined graph: {title} ({graph_id})")
            
            try:
                # Create the visualization
                fig = viz_manager.create_visualization(
                    dataset_name=dataset_name,
                    graph_id=graph_id
                )
                
                # Save the visualization
                filename = f"{graph_id}.{save_format}"
                filepath = os.path.join(dataset_dir, filename)
                fig.write_image(filepath)
                
                logger.info(f"Saved combined visualization to {filepath}")
            except Exception as e:
                logger.error(f"Error creating combined visualization: {str(e)}")
    
    logger.info(f"Visualization generation complete. All files saved to {viz_dir}")
    return viz_dir

def generate_html_dashboard(datasets=None, theme="default", output_file=None):
    """
    Generate an HTML dashboard with all visualizations
    
    Parameters:
    datasets (list): List of dataset names to include, or None for all
    theme (str): The Plotly theme to use
    output_file (str): Path to save the HTML file, or None for default
    """
    # Setup logging
    logger = setup_logging()
    
    # Initialize paths
    paths = ProjectPaths()
    
    # If no output file specified, create one
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(paths.reports_dir, f"dashboard_{timestamp}.html")
    
    # Initialize visualization manager
    viz_manager = VisualizationManager(theme=theme)
    
    # Load file descriptions
    with open(paths.file_descriptions_path, 'r') as f:
        file_descriptions = json.load(f)
    
    # If no specific datasets provided, use all
    if datasets is None:
        datasets = list(file_descriptions.keys())
    
    # Filter to only include datasets that exist in file_descriptions
    valid_datasets = [d for d in datasets if d in file_descriptions]
    
    if not valid_datasets:
        logger.error("No valid datasets found to include in dashboard")
        return
    
    # Create HTML content
    html_content = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        "    <title>Data Visualization Dashboard</title>",
        "    <meta charset=\"UTF-8\">",
        "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">",
        "    <script src=\"https://cdn.plot.ly/plotly-latest.min.js\"></script>",
        "    <style>",
        "        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }",
        "        .dashboard-title { text-align: center; margin-bottom: 30px; }",
        "        .section { margin-bottom: 40px; }",
        "        .section-title { margin-bottom: 20px; border-bottom: 1px solid #ddd; padding-bottom: 10px; }",
        "        .graph-container { height: 500px; margin-bottom: 30px; }",
        "        .flex-container { display: flex; flex-wrap: wrap; }",
        "        .flex-item { flex: 1 1 45%; min-width: 500px; margin: 10px; }",
        "    </style>",
        "</head>",
        "<body>",
        "    <div class=\"dashboard-title\">",
        f"        <h1>Data Visualization Dashboard</h1>",
        f"        <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>",
        "    </div>"
    ]
    
    # Process each dataset
    for dataset_name in valid_datasets:
        logger.info(f"Adding dataset to dashboard: {dataset_name}")
        
        # Get formatted title
        title = " ".join(word.capitalize() for word in dataset_name.split('_'))
        
        # Add section for this dataset
        html_content.extend([
            f"    <div class=\"section\" id=\"{dataset_name}\">",
            f"        <h2 class=\"section-title\">{title}</h2>"
        ])
        
        dataset_config = file_descriptions[dataset_name]
        visualization_config = dataset_config.get('visualization', {})
        
        # Add combined graphs first
        combined_graphs = visualization_config.get('combined_graphs', [])
        if combined_graphs:
            html_content.append("        <div class=\"flex-container\">")
            
            for graph_config in combined_graphs:
                graph_id = graph_config.get('id')
                graph_title = graph_config.get('title', f"{title} Combined")
                
                try:
                    # Create the visualization
                    fig = viz_manager.create_visualization(
                        dataset_name=dataset_name,
                        graph_id=graph_id
                    )
                    
                    # Convert to HTML div
                    graph_html = fig.to_html(
                        full_html=False,
                        include_plotlyjs=False,
                        div_id=f"graph_{graph_id}"
                    )
                    
                    html_content.extend([
                        f"            <div class=\"flex-item\">",
                        f"                <h3>{graph_title}</h3>",
                        f"                <div class=\"graph-container\" id=\"container_{graph_id}\">",
                        f"{graph_html}",
                        f"                </div>",
                        f"            </div>"
                    ])
                except Exception as e:
                    logger.error(f"Error creating combined graph {graph_id}: {str(e)}")
            
            html_content.append("        </div>")
        
        # Add individual graphs
        variables = visualization_config.get('variables', {})
        if variables:
            html_content.append("        <div class=\"flex-container\">")
            
            for var_name, var_config in variables.items():
                if var_config.get('visible', True):
                    graph_id = var_config.get('graph_id')
                    display_name = var_config.get('display_name', var_name)
                    
                    try:
                        # Create the visualization
                        fig = viz_manager.create_visualization(
                            dataset_name=dataset_name,
                            variable_names=[var_name],
                            graph_id=graph_id
                        )
                        
                        # Convert to HTML div
                        graph_html = fig.to_html(
                            full_html=False,
                            include_plotlyjs=False,
                            div_id=f"graph_{graph_id}"
                        )
                        
                        html_content.extend([
                            f"            <div class=\"flex-item\">",
                            f"                <h3>{display_name}</h3>",
                            f"                <div class=\"graph-container\" id=\"container_{graph_id}\">",
                            f"{graph_html}",
                            f"                </div>",
                            f"            </div>"
                        ])
                    except Exception as e:
                        logger.error(f"Error creating individual graph for {display_name}: {str(e)}")
            
            html_content.append("        </div>")
        
        # Close section
        html_content.append("    </div>")
    
    # Close HTML
    html_content.extend([
        "</body>",
        "</html>"
    ])
    
    # Write HTML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(html_content))
    
    logger.info(f"HTML dashboard saved to {output_file}")
    return output_file

if __name__ == "__main__":
    # Generate visualizations for all datasets
    generate_visualizations(
        theme="default",
        save_format="png"
    )
    
    # Generate an HTML dashboard
    generate_html_dashboard(
        theme="presentation"
    )