"""
File: visualization_utils.py
Directory: /content/drive/MyDrive/Colab Notebooks/automated_reporting/src/

Utilities for creating visualizations with consistent styling using
the layout configuration.
"""

import os
import json
import plotly.graph_objects as go
import plotly.express as px
from path_config import ProjectPaths

class VisualizationManager:
    def __init__(self, theme="default"):
        """
        Initialize the visualization manager with a selected theme
        
        Parameters:
        theme (str): The theme to use ('default', 'dark', 'print', 'presentation')
        """
        # Initialize paths
        self.paths = ProjectPaths()
        
        # Load layout configuration
        layout_config_path = os.path.join(self.paths.dictionary_dir, 'plotly_layout_config.json')
        with open(layout_config_path, 'r') as f:
            self.layout_config = json.load(f)
        
        # Set theme
        self.set_theme(theme)
        
        # Load file descriptions which contain visualization settings
        desc_path = self.paths.file_descriptions_path
        with open(desc_path, 'r') as f:
            self.file_descriptions = json.load(f)
    
    def set_theme(self, theme):
        """Set the current theme"""
        if theme not in self.layout_config['themes']:
            raise ValueError(f"Theme '{theme}' not found. Available themes: {list(self.layout_config['themes'].keys())}")
        
        self.current_theme = theme
        self.theme_layout = self.layout_config['themes'][theme]['layout']
        self.theme_traces = self.layout_config['themes'][theme]['traces']
    
    def get_trace_style(self, trace_type):
        """Get styling for a specific trace type"""
        if trace_type in self.theme_traces:
            return self.theme_traces[trace_type]
        return {}
    
    def apply_layout_settings(self, fig, title=None, xaxis_title=None, yaxis_title=None, 
                             legend_title=None, additional_layout=None):
        """
        Apply theme layout settings to a figure
        
        Parameters:
        fig: Plotly figure object
        title (str): Chart title
        xaxis_title (str): X-axis title
        yaxis_title (str): Y-axis title
        legend_title (str): Legend title
        additional_layout (dict): Additional layout settings to override defaults
        
        Returns:
        fig: Updated figure
        """
        # Start with theme layout
        layout = self.theme_layout.copy()
        
        # Update with provided titles
        if title:
            layout['title']['text'] = title
        
        if xaxis_title:
            layout['xaxis']['title']['text'] = xaxis_title
            
        if yaxis_title:
            layout['yaxis']['title']['text'] = yaxis_title
            
        if legend_title:
            layout['legend']['title'] = {"text": legend_title}
        
        # Override with any additional settings
        if additional_layout:
            # Handle nested dictionaries properly
            def deep_update(d, u):
                for k, v in u.items():
                    if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                        deep_update(d[k], v)
                    else:
                        d[k] = v
                return d
            
            layout = deep_update(layout, additional_layout)
        
        # Apply layout to figure
        fig.update_layout(**layout)
        
        return fig
    
    def create_visualization(self, dataset_name, variable_names=None, graph_id=None):
        """
        Create a visualization based on dataset and configuration in file_descriptions
        
        Parameters:
        dataset_name (str): Name of the dataset (without .csv extension)
        variable_names (list): List of variables to include (if None, use all)
        graph_id (str): ID of a specific graph configuration to use
        
        Returns:
        fig: Plotly figure
        """
        if dataset_name not in self.file_descriptions:
            raise ValueError(f"Dataset '{dataset_name}' not found in file descriptions")
        
        dataset_config = self.file_descriptions[dataset_name]
        
        # Load the dataset
        data_path = os.path.join(self.paths.processed_data_dir, f"{dataset_name}.pkl")
        df = pd.read_pickle(data_path)
        
        # If no variables specified, use all
        if not variable_names:
            variable_names = dataset_config['variable_names']
        
        # Find the graph configuration to use
        graph_config = None
        
        if graph_id:
            # Look for a specific combined graph
            for combined_graph in dataset_config['visualization']['combined_graphs']:
                if combined_graph['id'] == graph_id:
                    graph_config = combined_graph
                    break
            
            # If not found, check individual variable graphs
            if not graph_config:
                for var_name, var_config in dataset_config['visualization']['variables'].items():
                    if var_config['graph_id'] == graph_id:
                        graph_config = var_config['graph_config']
                        variable_names = [var_name]  # Only use this variable
                        break
        
        # If no specific graph found, use the first combined graph or create default
        if not graph_config:
            if 'combined_graphs' in dataset_config['visualization'] and dataset_config['visualization']['combined_graphs']:
                graph_config = dataset_config['visualization']['combined_graphs'][0]
            else:
                # Create a default graph config
                graph_config = {
                    'title': f"{dataset_name} Visualization",
                    'type': 'line',
                    'x_axis': {'title': 'Time Period'},
                    'y_axis': {'title': 'Value'}
                }
        
        # Create the figure
        fig = go.Figure()
        
        # Get the first column (usually the date/time column)
        x_column = df.columns[0]
        
        # Add each variable as a trace
        for var_name in variable_names:
            if var_name not in df.columns:
                print(f"Warning: Variable '{var_name}' not found in dataset")
                continue
            
            # Get variable-specific configuration
            var_config = dataset_config['visualization']['variables'].get(var_name, {})
            display_name = var_config.get('display_name', var_name)
            color = var_config.get('color', None)
            
            # Get trace styling based on graph type
            graph_type = graph_config.get('type', 'line')
            trace_style = self.get_trace_style(graph_type).copy()
            
            # Create the trace
            if graph_type == 'line':
                trace = go.Scatter(
                    x=df[x_column],
                    y=df[var_name],
                    name=display_name,
                    mode=trace_style.get('mode', 'lines+markers')
                )
            elif graph_type == 'bar':
                trace = go.Bar(
                    x=df[x_column],
                    y=df[var_name],
                    name=display_name
                )
            elif graph_type == 'area':
                trace = go.Scatter(
                    x=df[x_column],
                    y=df[var_name],
                    name=display_name,
                    fill='tozeroy',
                    mode='lines'
                )
            elif graph_type == 'scatter':
                trace = go.Scatter(
                    x=df[x_column],
                    y=df[var_name],
                    name=display_name,
                    mode='markers'
                )
            else:
                # Default to line
                trace = go.Scatter(
                    x=df[x_column],
                    y=df[var_name],
                    name=display_name
                )
            
            # Apply trace styling
            for key, value in trace_style.items():
                if key not in ['mode', 'hovertemplate']:  # These are handled separately
                    trace.update({key: value})
            
            # Set custom color if provided
            if color and 'line' in trace:
                trace.line.color = color
            elif color and 'marker' in trace:
                trace.marker.color = color
            
            # Add trace to figure
            fig.add_trace(trace)
        
        # Apply layout settings
        title = graph_config.get('title', f"{dataset_name} Visualization")
        xaxis_title = graph_config.get('x_axis', {}).get('title', 'Time Period')
        yaxis_title = graph_config.get('y_axis', {}).get('title', 'Value')
        
        # Additional layout settings from graph config
        additional_layout = graph_config.get('layout', {})
        
        # Apply layout
        fig = self.apply_layout_settings(
            fig, 
            title=title,
            xaxis_title=xaxis_title,
            yaxis_title=yaxis_title,
            additional_layout=additional_layout
        )
        
        return fig
    
    def save_visualization(self, fig, filename, format='png', width=None, height=None):
        """Save a visualization to file"""
        # Get download settings
        download_config = self.layout_config['customizations']['download']
        
        # Set default dimensions from config if not provided
        if width is None:
            width = download_config.get('width', 1200)
        if height is None:
            height = download_config.get('height', 800)
        
        # Create full path
        full_path = os.path.join(self.paths.visualizations_dir, filename)
        
        # Make sure the directory exists
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Save the figure
        fig.write_image(full_path, format=format, width=width, height=height, scale=download_config.get('scale', 2))
        
        print(f"Visualization saved to {full_path}")
        return full_path


# Example usage
if __name__ == "__main__":
    # Example of creating a visualization
    viz_manager = VisualizationManager(theme="default")
    
    # Create a visualization for a dataset
    fig = viz_manager.create_visualization(
        dataset_name="bbc_investeringsuitgaven_wegen_infra",
        graph_id="bbc_investeringsuitgaven_wegen_infra_combined"
    )
    
    # Save the visualization
    viz_manager.save_visualization(
        fig,
        filename="investments_all_provinces.png"
    )
    
    # Change theme and create another visualization
    viz_manager.set_theme("presentation")
    fig2 = viz_manager.create_visualization(
        dataset_name="bbc_investeringsuitgaven_wegen_infra",
        variable_names=["antwerpen", "limburg"]
    )
    
    # Save the visualization
    viz_manager.save_visualization(
        fig2,
        filename="investments_antwerp_limburg_presentation.png"
    )