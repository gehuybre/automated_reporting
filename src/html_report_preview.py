"""
File: html_report_preview.py
Directory: /content/drive/MyDrive/Colab Notebooks/automated_reporting/src/

This script generates HTML report previews combining data tables,
visualizations, and analysis insights.
"""

import os
import json
import pandas as pd
import logging
from datetime import datetime
from pathlib import Path

# Import project modules
from path_config import ProjectPaths
from html_table_generator import HTMLTableGenerator
from visualization_utils import VisualizationManager

def setup_logging():
    """Setup logging configuration"""
    paths = ProjectPaths()
    log_dir = paths.logs_dir
    
    # Create logs directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    log_file = os.path.join(log_dir, 'html_report_preview.log')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

class HTMLReportPreview:
    """Class to generate HTML report previews for datasets"""
    
    def __init__(self, theme="default"):
        """
        Initialize HTML report preview generator
        
        Parameters:
        theme (str): Visualization theme to use
        """
        self.logger = setup_logging()
        self.paths = ProjectPaths()
        self.theme = theme
        
        # Initialize components
        self.table_generator = HTMLTableGenerator()
        self.viz_manager = VisualizationManager(theme=theme)
        
        # Create output directory
        os.makedirs(self.paths.html_reports_dir, exist_ok=True)
        
        # Load file descriptions
        try:
            with open(self.paths.file_descriptions_path, 'r') as f:
                self.file_descriptions = json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading file descriptions: {str(e)}")
            self.file_descriptions = {}
    
    def _get_report_header(self, title):
        """Generate the HTML header section with styles"""
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title} - Report Preview</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                header {{
                    text-align: center;
                    margin-bottom: 30px;
                    padding-bottom: 20px;
                    border-bottom: 1px solid #eee;
                }}
                h1 {{
                    color: #2c3e50;
                }}
                h2 {{
                    color: #3498db;
                    border-bottom: 1px solid #eee;
                    padding-bottom: 10px;
                    margin-top: 30px;
                }}
                h3 {{
                    color: #2980b9;
                    margin-top: 25px;
                }}
                h4 {{
                    color: #555;
                }}
                .section {{
                    margin-bottom: 40px;
                }}
                .viz-section {{
                    margin-bottom: 30px;
                }}
                .chart-container {{
                    margin-bottom: 40px;
                    border: 1px solid #eee;
                    border-radius: 5px;
                    padding: 20px;
                    background-color: #fafafa;
                }}
                .chart-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(500px, 1fr));
                    gap: 20px;
                    margin-top: 20px;
                }}
                .chart-item {{
                    border: 1px solid #eee;
                    border-radius: 5px;
                    padding: 15px;
                    background-color: #fafafa;
                }}
                table.data-table {{
                    width: 100%;
                    border-collapse: collapse;
                    font-family: Arial, sans-serif;
                    margin-bottom: 20px;
                }}
                .data-table th, .data-table td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: right;
                }}
                .data-table th {{
                    background-color: #f2f2f2;
                    text-align: center;
                    font-weight: bold;
                }}
                .data-table tr:nth-child(even) {{
                    background-color: #f9f9f9;
                }}
                .data-table tr:hover {{
                    background-color: #f0f0f0;
                }}
                .data-table .date-column {{
                    text-align: left;
                    font-weight: bold;
                }}
                .positive-change {{
                    color: green;
                }}
                .negative-change {{
                    color: red;
                }}
                .note {{
                    font-size: 0.9em;
                    font-style: italic;
                    color: #666;
                    margin-top: 10px;
                }}
                footer {{
                    text-align: center;
                    margin-top: 50px;
                    padding-top: 20px;
                    border-top: 1px solid #eee;
                    font-size: 0.9em;
                    color: #777;
                }}
            </style>
        </head>
        <body>
            <header>
                <h1>{title} - Analysis Report</h1>
                <p>This report provides an overview of {title} data with visualizations and analysis.</p>
            </header>
            <div class="report-container">
        """
    
    def _get_report_footer(self):
        """Generate the HTML footer section"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"""
            </div>
            <footer>
                <p>Generated on {timestamp}</p>
                <p>Automated Reporting System</p>
            </footer>
        </body>
        </html>
        """
    
    def _load_dataset(self, dataset_name):
        """Load a dataset and return as DataFrame"""
        # Try to load from processed data
        processed_path = os.path.join(self.paths.processed_data_dir, f"{dataset_name}.csv")
        if os.path.exists(processed_path):
            return pd.read_csv(processed_path)
        
        # Try raw data as fallback
        raw_path = os.path.join(self.paths.raw_data_dir, f"{dataset_name}.csv")
        if os.path.exists(raw_path):
            return pd.read_csv(raw_path)
        
        self.logger.error(f"Could not find data file for {dataset_name}")
        return None
    
    def _generate_data_section(self, dataset_name, include_yoy=True):
        """Generate the data table section"""
        html = []
        html.append('<div class="section data-section">')
        html.append('<h2>Data Overview</h2>')
        
        table_html = self.table_generator.generate_data_table_html(
            dataset_name=dataset_name,
            include_yoy=include_yoy
        )
        
        html.append(table_html)
        
        html.append('<p class="note">Table shows the raw data values and year-over-year percentage changes.</p>')
        html.append('</div>')
        
        return '\n'.join(html)
    
    def _generate_visualization_section(self, dataset_name):
        """Generate the visualization section"""
        if dataset_name not in self.file_descriptions:
            self.logger.error(f"Dataset {dataset_name} not found in file descriptions")
            return "<p>Error: Dataset not found in file descriptions</p>"
        
        dataset_config = self.file_descriptions[dataset_name]
        viz_config = dataset_config.get('visualization', {})
        
        html = []
        html.append('<div class="section viz-section">')
        html.append('<h2>Visualizations</h2>')
        
        # Combined visualizations
        combined_graphs = viz_config.get('combined_graphs', [])
        if combined_graphs:
            html.append('<h3>Combined Visualizations</h3>')
            html.append('<div class="chart-grid">')
            
            for graph_config in combined_graphs:
                graph_id = graph_config.get('id')
                title = graph_config.get('title', 'Combined Visualization')
                
                try:
                    fig = self.viz_manager.create_visualization(
                        dataset_name=dataset_name,
                        graph_id=graph_id
                    )
                    
                    # Convert to HTML
                    graph_html = fig.to_html(
                        full_html=False,
                        include_plotlyjs=False,
                        div_id=f"graph_{graph_id}"
                    )
                    
                    html.append(f'<div class="chart-item" id="chart_{graph_id}">')
                    html.append(f'<h4>{title}</h4>')
                    html.append(graph_html)
                    html.append('</div>')
                    
                except Exception as e:
                    self.logger.error(f"Error generating visualization for {graph_id}: {str(e)}")
                    html.append(f'<div class="chart-item"><p>Error generating visualization: {str(e)}</p></div>')
            
            html.append('</div>')
        
        # Individual visualizations
        variables = viz_config.get('variables', {})
        if variables:
            html.append('<h3>Individual Variables</h3>')
            html.append('<div class="chart-grid">')
            
            for var_name, var_config in variables.items():
                if var_config.get('visible', True):
                    graph_id = var_config.get('graph_id')
                    display_name = var_config.get('display_name', var_name)
                    
                    try:
                        fig = self.viz_manager.create_visualization(
                            dataset_name=dataset_name,
                            variable_names=[var_name],
                            graph_id=graph_id
                        )
                        
                        # Convert to HTML
                        graph_html = fig.to_html(
                            full_html=False,
                            include_plotlyjs=False,
                            div_id=f"graph_{graph_id}"
                        )
                        
                        html.append(f'<div class="chart-item" id="chart_{graph_id}">')
                        html.append(f'<h4>{display_name}</h4>')
                        html.append(graph_html)
                        html.append('</div>')
                        
                    except Exception as e:
                        self.logger.error(f"Error generating visualization for {var_name}: {str(e)}")
                        html.append(f'<div class="chart-item"><p>Error generating visualization: {str(e)}</p></div>')
            
            html.append('</div>')
        
        html.append('</div>')
        
        return '\n'.join(html)
    
    def _generate_analysis_section(self, dataset_name):
        """Generate the analysis section with insights"""
        html = []
        html.append('<div class="section analysis-section">')
        html.append('<h2>Analysis & Insights</h2>')
        
        # Try to load recent statistics files
        statistics_dir = os.path.join(self.paths.data_dir, 'statistics')
        if os.path.exists(statistics_dir):
            # Find the most recent statistics JSON file
            stat_files = [f for f in os.listdir(statistics_dir) if f.startswith('statistics_') and f.endswith('.json')]
            if stat_files:
                # Sort by modification time, newest first
                stat_files.sort(key=lambda x: os.path.getmtime(os.path.join(statistics_dir, x)), reverse=True)
                latest_stats_file = os.path.join(statistics_dir, stat_files[0])
                
                try:
                    with open(latest_stats_file, 'r') as f:
                        stats_data = json.load(f)
                    
                    if dataset_name in stats_data:
                        dataset_stats = stats_data[dataset_name]
                        
                        # Dataset overview
                        html.append('<h3>Statistical Overview</h3>')
                        html.append('<p>Key statistics for each variable in the dataset:</p>')
                        
                        # Add variable statistics
                        html.append('<div class="stats-grid">')
                        for var_name, var_stats in dataset_stats['variables'].items():
                            display_name = var_stats.get('display_name', var_name)
                            
                            html.append(f'<div class="stats-item">')
                            html.append(f'<h4>{display_name}</h4>')
                            
                            # Min/Max values
                            min_value = var_stats['minimum']['value']
                            min_date = var_stats['minimum']['date']
                            max_value = var_stats['maximum']['value']
                            max_date = var_stats['maximum']['date']
                            
                            html.append('<ul>')
                            html.append(f'<li>Minimum: {min_value:,.0f} (occurred in {min_date})</li>')
                            html.append(f'<li>Maximum: {max_value:,.0f} (occurred in {max_date})</li>')
                            
                            # Recent YoY changes
                            yoy_changes = var_stats.get('year_over_year_changes', {})
                            if yoy_changes:
                                # Get the most recent years
                                recent_years = sorted(yoy_changes.keys())[-3:]
                                
                                html.append('<li>Recent year-over-year changes:')
                                html.append('<ul>')
                                for year in recent_years:
                                    change = yoy_changes[year]
                                    color_class = 'positive-change' if change >= 0 else 'negative-change'
                                    html.append(f'<li>{year}: <span class="{color_class}">{change:+.1f}%</span></li>')
                                html.append('</ul>')
                                html.append('</li>')
                            
                            html.append('</ul>')
                            html.append('</div>')
                        
                        html.append('</div>')
                        
                        # Add analysis insights section
                        html.append('<h3>Key Insights</h3>')
                        
                        # Add some generic insights based on the statistics
                        html.append('<div class="insights">')
                        
                        # Find variable with highest recent growth
                        max_growth_var = None
                        max_growth_rate = -float('inf')
                        for var_name, var_stats in dataset_stats['variables'].items():
                            yoy_changes = var_stats.get('year_over_year_changes', {})
                            if yoy_changes:
                                recent_years = sorted(yoy_changes.keys())
                                if recent_years:
                                    latest_change = yoy_changes[recent_years[-1]]
                                    if latest_change > max_growth_rate:
                                        max_growth_rate = latest_change
                                        max_growth_var = var_stats.get('display_name', var_name)
                        
                        if max_growth_var:
                            growth_type = "growth" if max_growth_rate > 0 else "decline"
                            html.append(f'<p><strong>{max_growth_var}</strong> showed the highest recent {growth_type} '
                                        f'rate of <span class="{"positive-change" if max_growth_rate > 0 else "negative-change"}">'
                                        f'{max_growth_rate:+.1f}%</span> in the latest period.</p>')
                        
                        # Check for any significant drops
                        significant_drops = []
                        for var_name, var_stats in dataset_stats['variables'].items():
                            yoy_changes = var_stats.get('year_over_year_changes', {})
                            for year, change in yoy_changes.items():
                                if change < -15:  # Consider drops greater than 15% significant
                                    significant_drops.append((var_stats.get('display_name', var_name), year, change))
                        
                        if significant_drops:
                            # Sort by magnitude of drop
                            significant_drops.sort(key=lambda x: x[2])
                            
                            html.append('<p>Significant drops in activity were observed in:</p>')
                            html.append('<ul>')
                            for var, year, change in significant_drops[:3]:  # Show top 3 most significant drops
                                html.append(f'<li><strong>{var}</strong> in {year}: <span class="negative-change">'
                                            f'{change:.1f}%</span></li>')
                            html.append('</ul>')
                            
                            if len(significant_drops) > 3:
                                html.append(f'<p class="note">And {len(significant_drops) - 3} more significant drops.</p>')
                        
                        html.append('</div>')
                
                except Exception as e:
                    self.logger.error(f"Error processing statistics: {str(e)}")
                    html.append(f'<p>Error loading statistics: {str(e)}</p>')
            else:
                html.append('<p>No statistics files found. Run data_statistics.py to generate statistics.</p>')
        else:
            html.append('<p>Statistics directory not found. Use the data_statistics.py script to generate statistics.</p>')
        
        html.append('</div>')
        
        return '\n'.join(html)
    
    def generate_report_preview(self, dataset_name, include_yoy=True, include_viz=True, include_analysis=True):
        """
        Generate an HTML report preview for a dataset
        
        Parameters:
        dataset_name (str): Name of the dataset to visualize
        include_yoy (bool): Whether to include year-over-year calculations in tables
        include_viz (bool): Whether to include visualizations
        include_analysis (bool): Whether to include data analysis
        
        Returns:
        str: Path to the generated HTML file
        """
        if dataset_name not in self.file_descriptions:
            self.logger.error(f"Dataset {dataset_name} not found in file descriptions")
            return None
        
        # Create formatted title
        title = " ".join(word.capitalize() for word in dataset_name.split('_'))
        
        # Start building HTML
        html = []
        
        # Add header
        html.append(self._get_report_header(title))
        
        # Add data section
        try:
            html.append(self._generate_data_section(dataset_name, include_yoy))
        except Exception as e:
            self.logger.error(f"Error generating data section: {str(e)}")
            html.append(f'<div class="section"><p>Error generating data section: {str(e)}</p></div>')
        
        # Add visualization section
        if include_viz:
            try:
                html.append(self._generate_visualization_section(dataset_name))
            except Exception as e:
                self.logger.error(f"Error generating visualization section: {str(e)}")
                html.append(f'<div class="section"><p>Error generating visualization section: {str(e)}</p></div>')
        
        # Add analysis section
        if include_analysis:
            try:
                html.append(self._generate_analysis_section(dataset_name))
            except Exception as e:
                self.logger.error(f"Error generating analysis section: {str(e)}")
                html.append(f'<div class="section"><p>Error generating analysis section: {str(e)}</p></div>')
        
        # Add footer
        html.append(self._get_report_footer())
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(self.paths.html_reports_dir, f"{dataset_name}_report_{timestamp}.html")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(html))
        
        self.logger.info(f"Generated report preview: {output_path}")
        return output_path


if __name__ == "__main__":
    # Example usage
    report_generator = HTMLReportPreview(theme="default")
    
    # Generate preview for a dataset
    report_path = report_generator.generate_report_preview(
        dataset_name="bbc_investeringsuitgaven_wegen_infra",
        include_yoy=True,
        include_viz=True,
        include_analysis=True
    )
    
    print(f"Report generated: {report_path}")