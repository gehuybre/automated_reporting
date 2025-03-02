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