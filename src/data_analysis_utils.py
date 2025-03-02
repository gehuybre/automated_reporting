"""
File: data_analysis_utils.py
Directory: /content/drive/MyDrive/Colab Notebooks/automated_reporting/src/

Utilities for analyzing data, calculating metrics, and generating insights
that can be included in reports.
"""

import os
import pandas as pd
import numpy as np
import json
import logging
from pathlib import Path
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
    log_file = os.path.join(log_dir, 'data_analysis.log')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

class DataAnalyzer:
    """Class for analyzing data and generating insights"""
    
    def __init__(self):
        """Initialize the data analyzer"""
        self.logger = setup_logging()
        self.paths = ProjectPaths()
        
        # Create analysis output directory
        self.analysis_dir = os.path.join(self.paths.data_dir, "analysis")
        os.makedirs(self.analysis_dir, exist_ok=True)
        
        # Load file descriptions
        try:
            with open(self.paths.file_descriptions_path, 'r') as f:
                self.file_descriptions = json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading file descriptions: {str(e)}")
            self.file_descriptions = {}
    
    def load_dataset(self, dataset_name):
        """
        Load a dataset from processed or raw data
        
        Parameters:
        dataset_name (str): Name of the dataset
        
        Returns:
        DataFrame: Loaded dataset or None if not found
        """
        # Try to load from processed data first
        processed_path = os.path.join(self.paths.processed_data_dir, f"{dataset_name}.csv")
        if os.path.exists(processed_path):
            try:
                df = pd.read_csv(processed_path)
                if not df.empty:
                    return df
            except Exception as e:
                self.logger.warning(f"Error loading processed data for {dataset_name}: {str(e)}")
        
        # Try raw data as fallback
        raw_path = os.path.join(self.paths.raw_data_dir, f"{dataset_name}.csv")
        if os.path.exists(raw_path):
            try:
                df = pd.read_csv(raw_path)
                if not df.empty:
                    return df
            except Exception as e:
                self.logger.error(f"Error loading raw data for {dataset_name}: {str(e)}")
        
        self.logger.error(f"Could not find data for {dataset_name}")
        return None
    
    def calculate_yoy_changes(self, dataset_name, save_results=True):
        """
        Calculate year-over-year percentage changes for all numeric columns
        
        Parameters:
        dataset_name (str): Name of the dataset
        save_results (bool): Whether to save results to file
        
        Returns:
        tuple: (original_df, yoy_df) - Original data and YoY changes
        """
        # Load the dataset
        df = self.load_dataset(dataset_name)
        if df is None:
            return None, None
        
        # Make a copy to avoid modifying the original
        df_copy = df.copy()
        
        # Get the date column (assumed to be the first column)
        date_col = df_copy.columns[0]
        
        # Convert to datetime if not already
        if not pd.api.types.is_datetime64_dtype(df_copy[date_col]):
            try:
                df_copy[date_col] = pd.to_datetime(df_copy[date_col])
            except:
                # If conversion fails, try to extract year directly from string
                self.logger.warning(f"Could not convert {date_col} to datetime, will try to extract year")
        
        # Extract year from date or directly from string
        try:
            if pd.api.types.is_datetime64_dtype(df_copy[date_col]):
                df_copy['year'] = df_copy[date_col].dt.year
            else:
                # Try to extract year from string (e.g., "2015-01-01" or "2015")
                df_copy['year'] = df_copy[date_col].str.extract(r'(\d{4})').astype(int)
        except Exception as e:
            self.logger.error(f"Could not extract year from {date_col}: {str(e)}")
            return df, None
        
        # Calculate YoY changes for each numeric column
        yoy_df = pd.DataFrame()
        yoy_df[date_col] = df_copy[date_col]
        
        # For each numeric column, calculate the percentage change
        for col in df_copy.columns:
            if col not in [date_col, 'year'] and pd.api.types.is_numeric_dtype(df_copy[col]):
                # Calculate year-over-year changes
                df_copy[f'{col}_yoy'] = df_copy.groupby('year')[col].transform(
                    lambda x: x.pct_change(periods=1) * 100
                )
                
                # Add to YoY DataFrame
                yoy_df[col] = df_copy[col]
                yoy_df[f'{col}_yoy'] = df_copy[f'{col}_yoy']
        
        # Save results if requested
        if save_results:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(self.analysis_dir, f"{dataset_name}_yoy_{timestamp}.csv")
            yoy_df.to_csv(output_path, index=False)
            self.logger.info(f"Saved YoY analysis for {dataset_name} to {output_path}")
        
        return df, yoy_df
    
    def calculate_summary_statistics(self, dataset_name, save_results=True):
        """
        Calculate summary statistics for a dataset
        
        Parameters:
        dataset_name (str): Name of the dataset
        save_results (bool): Whether to save results to file
        
        Returns:
        dict: Summary statistics by variable
        """
        # Load the dataset
        df = self.load_dataset(dataset_name)
        if df is None:
            return None
        
        # Get the date column (assumed to be the first column)
        date_col = df.columns[0]
        
        # Initialize summary statistics
        summary = {}
        
        # Get variable display names if available
        display_names = {}
        if dataset_name in self.file_descriptions:
            dataset_config = self.file_descriptions[dataset_name]
            if 'visualization' in dataset_config and 'variables' in dataset_config['visualization']:
                for var_name, var_config in dataset_config['visualization']['variables'].items():
                    display_names[var_name] = var_config.get('display_name', var_name)
        
        # Calculate statistics for each numeric column
        for col in df.columns:
            if col != date_col and pd.api.types.is_numeric_dtype(df[col]):
                # Get display name for the variable
                display_name = display_names.get(col, col)
                
                # Calculate basic statistics
                col_stats = {
                    'display_name': display_name,
                    'min': df[col].min(),
                    'max': df[col].max(),
                    'mean': df[col].mean(),
                    'median': df[col].median(),
                    'std_dev': df[col].std(),
                    'total': df[col].sum(),
                    'count': df[col].count()
                }
                
                # Find year with highest and lowest values
                try:
                    if pd.api.types.is_datetime64_dtype(df[date_col]):
                        max_year = df.loc[df[col].idxmax(), date_col].year
                        min_year = df.loc[df[col].idxmin(), date_col].year
                    else:
                        # Extract year from string date
                        max_date = df.loc[df[col].idxmax(), date_col]
                        min_date = df.loc[df[col].idxmin(), date_col]
                        max_year = int(str(max_date)[:4])  # Extract first 4 chars as year
                        min_year = int(str(min_date)[:4])
                    
                    col_stats['max_year'] = max_year
                    col_stats['min_year'] = min_year
                except:
                    # In case of error, just use the raw date value
                    col_stats['max_date'] = df.loc[df[col].idxmax(), date_col]
                    col_stats['min_date'] = df.loc[df[col].idxmin(), date_col]
                
                # Calculate compound annual growth rate (if at least 2 data points)
                if len(df) >= 2:
                    try:
                        # Sort by date to ensure first/last are correct
                        sorted_df = df.sort_values(by=date_col)
                        first_value = sorted_df[col].iloc[0]
                        last_value = sorted_df[col].iloc[-1]
                        num_years = len(sorted_df) - 1  # Assume annual data
                        
                        if first_value > 0 and last_value > 0:
                            cagr = (((last_value / first_value) ** (1 / num_years)) - 1) * 100
                            col_stats['cagr'] = cagr
                    except Exception as e:
                        self.logger.warning(f"Could not calculate CAGR for {col}: {str(e)}")
                
                summary[col] = col_stats
        
        # Add overall dataset statistics
        summary['_dataset'] = {
            'name': dataset_name,
            'display_name': " ".join(word.capitalize() for word in dataset_name.split('_')),
            'num_variables': len(df.columns) - 1,  # Exclude date column
            'num_observations': len(df),
            'years_covered': len(df['year'].unique()) if 'year' in df else len(df),
            'date_first': df[date_col].min(),
            'date_last': df[date_col].max()
        }
        
        # Save results if requested
        if save_results:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(self.analysis_dir, f"{dataset_name}_summary_{timestamp}.json")
            with open(output_path, 'w') as f:
                json.dump(summary, f, indent=4, default=str)  # Use default=str to handle datetime objects
            self.logger.info(f"Saved summary statistics for {dataset_name} to {output_path}")
        
        return summary
    
    def identify_trends(self, dataset_name, window=3, save_results=True):
        """
        Identify trends and inflection points in the data
        
        Parameters:
        dataset_name (str): Name of the dataset
        window (int): Rolling window size for trend detection
        save_results (bool): Whether to save results to file
        
        Returns:
        dict: Trend analysis results
        """
        # Load the dataset
        df = self.load_dataset(dataset_name)
        if df is None:
            return None
        
        # Get the date column (assumed to be the first column)
        date_col = df.columns[0]
        
        # Convert to datetime if not already
        if not pd.api.types.is_datetime64_dtype(df[date_col]):
            try:
                df[date_col] = pd.to_datetime(df[date_col])
            except:
                # If conversion fails, proceed with string dates
                pass
        
        # Initialize trend results
        trends = {}
        
        # Analyze each numeric column
        for col in df.columns:
            if col != date_col and pd.api.types.is_numeric_dtype(df[col]):
                # Calculate rolling average
                rolling_avg = df[col].rolling(window=window, min_periods=1).mean()
                
                # Calculate trend direction (1 for up, -1 for down, 0 for flat)
                trend_direction = np.sign(rolling_avg.diff())
                
                # Find inflection points (where trend changes direction)
                inflection_points = []
                prev_direction = None
                
                for i, (date, direction) in enumerate(zip(df[date_col], trend_direction)):
                    if i > 0 and direction != prev_direction and not pd.isna(direction) and not pd.isna(prev_direction):
                        inflection_points.append({
                            'date': date,
                            'value': df[col].iloc[i],
                            'direction': 'up' if direction > 0 else 'down' if direction < 0 else 'flat'
                        })
                    prev_direction = direction
                
                # Calculate current trend (based on last window periods)
                current_trend = {
                    'direction': 'up' if trend_direction.iloc[-1] > 0 else 'down' if trend_direction.iloc[-1] < 0 else 'flat',
                    'momentum': abs(rolling_avg.diff().iloc[-1] / rolling_avg.iloc[-1] * 100) if rolling_avg.iloc[-1] != 0 else 0
                }
                
                # Store results for this column
                trends[col] = {
                    'rolling_avg': rolling_avg.tolist(),
                    'inflection_points': inflection_points,
                    'current_trend': current_trend,
                }
        
        # Save results if requested
        if save_results:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(self.analysis_dir, f"{dataset_name}_trends_{timestamp}.json")
            
            # Convert to serializable format
            serializable_trends = {}
            for col, col_trends in trends.items():
                serializable_trends[col] = {
                    'rolling_avg': col_trends['rolling_avg'],
                    'inflection_points': [
                        {
                            'date': str(p['date']),
                            'value': p['value'],
                            'direction': p['direction']
                        } for p in col_trends['inflection_points']
                    ],
                    'current_trend': col_trends['current_trend']
                }
            
            with open(output_path, 'w') as f:
                json.dump(serializable_trends, f, indent=4)
            
            self.logger.info(f"Saved trend analysis for {dataset_name} to {output_path}")
        
        return trends
    
    def generate_insights(self, dataset_name, save_results=True):
        """
        Generate text insights about the data that can be included in reports
        
        Parameters:
        dataset_name (str): Name of the dataset
        save_results (bool): Whether to save results to file
        
        Returns:
        dict: Text insights for different aspects of the data
        """
        # Load the dataset
        df = self.load_dataset(dataset_name)
        if df is None:
            return None
        
        # Run other analyses to use for insights
        _, yoy_df = self.calculate_yoy_changes(dataset_name, save_results=False)
        summary = self.calculate_summary_statistics(dataset_name, save_results=False)
        trends = self.identify_trends(dataset_name, save_results=False)
        
        # Get the date column (assumed to be the first column)
        date_col = df.columns[0]
        
        # Get variable display names if available
        display_names = {}
        if dataset_name in self.file_descriptions:
            dataset_config = self.file_descriptions[dataset_name]
            if 'visualization' in dataset_config and 'variables' in dataset_config['visualization']:
                for var_name, var_config in dataset_config['visualization']['variables'].items():
                    display_names[var_name] = var_config.get('display_name', var_name)
        
        # Generate insights
        insights = {
            'overview': [],  # Overview of the entire dataset
            'variables': {},  # Insights for each variable
            'comparisons': [],  # Comparisons between variables
            'recommendations': []  # Recommended actions or further analysis
        }
        
        # Overall dataset insights
        dataset_title = " ".join(word.capitalize() for word in dataset_name.split('_'))
        
        if summary and '_dataset' in summary:
            ds_summary = summary['_dataset']
            insights['overview'].append(
                f"This analysis covers {ds_summary['display_name']} data from "
                f"{ds_summary['date_first']} to {ds_summary['date_last']}, "
                f"spanning {ds_summary['num_observations']} observations across "
                f"{ds_summary['num_variables']} variables."
            )
        
        # Generate insights for each variable
        for col in df.columns:
            if col != date_col and pd.api.types.is_numeric_dtype(df[col]):
                # Get display name
                display_name = display_names.get(col, col)
                variable_insights = []
                
                # Get summary statistics for this variable
                if summary and col in summary:
                    stats = summary[col]
                    
                    # Basic summary
                    variable_insights.append(
                        f"{display_name} ranges from {stats['min']:,.0f} to {stats['max']:,.0f}, "
                        f"with an average of {stats['mean']:,.0f}."
                    )
                    
                    # Period with highest/lowest values
                    if 'max_year' in stats and 'min_year' in stats:
                        variable_insights.append(
                            f"The highest value was recorded in {stats['max_year']}, "
                            f"while the lowest value was in {stats['min_year']}."
                        )
                    
                    # Growth rate
                    if 'cagr' in stats:
                        growth_text = "growth" if stats['cagr'] > 0 else "decline"
                        variable_insights.append(
                            f"{display_name} shows a compound annual {growth_text} rate of "
                            f"{stats['cagr']:.1f}% over the analyzed period."
                        )
                
                # Recent trends
                if trends and col in trends:
                    col_trends = trends[col]
                    current_trend = col_trends['current_trend']
                    
                    trend_text = "increasing" if current_trend['direction'] == 'up' else \
                                "decreasing" if current_trend['direction'] == 'down' else "stable"
                    
                    variable_insights.append(
                        f"The current trend for {display_name} is {trend_text}."
                    )
                    
                    # Inflection points
                    if col_trends['inflection_points']:
                        recent_points = col_trends['inflection_points'][-2:] if len(col_trends['inflection_points']) > 1 else col_trends['inflection_points']
                        for point in recent_points:
                            variable_insights.append(
                                f"A trend change to {point['direction']} was detected at {point['date']}."
                            )
                
                # Recent YoY changes
                if yoy_df is not None:
                    yoy_col = f'{col}_yoy'
                    if yoy_col in yoy_df.columns:
                        # Get most recent YoY change
                        recent_yoy = yoy_df[yoy_col].iloc[-1]
                        if not pd.isna(recent_yoy):
                            change_text = "increase" if recent_yoy > 0 else "decrease"
                            variable_insights.append(
                                f"The most recent year-over-year {change_text} for {display_name} was {recent_yoy:.1f}%."
                            )
                
                # Store insights for this variable
                insights['variables'][col] = variable_insights
        
        # Generate comparisons between variables
        if len(df.columns) > 2:  # Only if there are at least 2 variables
            numeric_cols = [col for col in df.columns if col != date_col and pd.api.types.is_numeric_dtype(df[col])]
            
            if len(numeric_cols) >= 2:
                # Find variable with highest growth
                if yoy_df is not None:
                    yoy_cols = [col for col in yoy_df.columns if col.endswith('_yoy')]
                    if yoy_cols:
                        # Calculate average YoY change for each variable
                        avg_yoy_changes = {}
                        for yoy_col in yoy_cols:
                            base_col = yoy_col.replace('_yoy', '')
                            avg_yoy = yoy_df[yoy_col].mean()
                            if not pd.isna(avg_yoy):
                                avg_yoy_changes[base_col] = avg_yoy
                        
                        if avg_yoy_changes:
                            # Find max and min average YoY
                            max_col = max(avg_yoy_changes, key=avg_yoy_changes.get)
                            min_col = min(avg_yoy_changes, key=avg_yoy_changes.get)
                            
                            max_display = display_names.get(max_col, max_col)
                            min_display = display_names.get(min_col, min_col)
                            
                            insights['comparisons'].append(
                                f"{max_display} shows the highest average growth rate at {avg_yoy_changes[max_col]:.1f}%, "
                                f"while {min_display} has the lowest at {avg_yoy_changes[min_col]:.1f}%."
                            )
                
                # Find correlations between variables
                corr_matrix = df[numeric_cols].corr()
                
                # Find strongest positive and negative correlations
                strong_correlations = []
                
                for i in range(len(numeric_cols)):
                    for j in range(i+1, len(numeric_cols)):
                        col1, col2 = numeric_cols[i], numeric_cols[j]
                        corr = corr_matrix.loc[col1, col2]
                        
                        if abs(corr) > 0.7:  # Only strong correlations
                            display1 = display_names.get(col1, col1)
                            display2 = display_names.get(col2, col2)
                            
                            corr_type = "positive" if corr > 0 else "negative"
                            strong_correlations.append((display1, display2, corr, corr_type))
                
                if strong_correlations:
                    # Sort by absolute correlation strength
                    strong_correlations.sort(key=lambda x: abs(x[2]), reverse=True)
                    
                    # Add top correlations to insights
                    for display1, display2, corr, corr_type in strong_correlations[:2]:  # Limit to top 2
                        insights['comparisons'].append(
                            f"There is a strong {corr_type} correlation ({corr:.2f}) between "
                            f"{display1} and {display2}."
                        )
        
        # Generate recommendations
        insights['recommendations'].append(
            f"Consider monitoring the trends in {dataset_title} data on a quarterly basis."
        )
        
        if any(col.endswith('_yoy') for col in yoy_df.columns if yoy_df is not None):
            insights['recommendations'].append(
                "Pay special attention to variables with consistent year-over-year growth patterns."
            )
        
        # Add more specific recommendations based on trends
        if trends:
            # Find variables with recent trend changes
            recent_changes = []
            for col, col_trends in trends.items():
                if col_trends['inflection_points'] and len(col_trends['inflection_points']) > 0:
                    # Check if most recent inflection point is within last 3 periods
                    recent_point = col_trends['inflection_points'][-1]
                    display_name = display_names.get(col, col)
                    recent_changes.append((display_name, recent_point['direction']))
            
            if recent_changes:
                insights['recommendations'].append(
                    "Investigate the factors behind recent trend changes in " + 
                    ", ".join(f"{name} ({direction})" for name, direction in recent_changes[:3])
                )
        
        # Save results if requested
        if save_results:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(self.analysis_dir, f"{dataset_name}_insights_{timestamp}.json")
            
            with open(output_path, 'w') as f:
                json.dump(insights, f, indent=4)
            
            self.logger.info(f"Saved insights for {dataset_name} to {output_path}")
        
        return insights


if __name__ == "__main__":
    # Example usage
    analyzer = DataAnalyzer()
    
    # Process a dataset
    dataset_name = "bbc_investeringsuitgaven_wegen_infra"
    
    # Calculate YoY changes
    print(f"Calculating YoY changes for {dataset_name}...")
    df, yoy_df = analyzer.calculate_yoy_changes(dataset_name)
    
    # Calculate summary statistics
    print(f"Calculating summary statistics for {dataset_name}...")
    summary = analyzer.calculate_summary_statistics(dataset_name)
    
    # Identify trends
    print(f"Identifying trends for {dataset_name}...")
    trends = analyzer.identify_trends(dataset_name)
    
    # Generate insights
    print(f"Generating insights for {dataset_name}...")
    insights = analyzer.generate_insights(dataset_name)
    
    # Print some sample insights
    if insights:
        print("\nSample insights:")
        for insight in insights['overview']:
            print(f"- {insight}")
            
        if insights['variables']:
            var_name = list(insights['variables'].keys())[0]
            print(f"\nInsights for {var_name}:")
            for insight in insights['variables'][var_name]:
                print(f"- {insight}")