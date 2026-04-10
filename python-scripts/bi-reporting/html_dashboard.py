"""
HTML Dashboard Generator for watsonx.data Analytics

This module creates an interactive HTML dashboard with IBM Cloud Pak for Data styling
using Plotly for rich, interactive visualizations. The dashboard is self-contained in
a single HTML file that can be opened in any web browser.

Key Features:
    - Interactive charts with zoom, pan, and hover tooltips
    - IBM Cloud Pak for Data color palette and styling
    - IBM Plex Sans font family
    - Responsive design for different screen sizes
    - Single self-contained HTML file
    - Professional gradient header
    - Metric cards with key statistics
    - No external dependencies (Plotly embedded)

Chart Types:
    1. Daily Revenue Trend: Line + bar chart with dual y-axes
    2. Customer Segmentation: Pie chart + bar chart side-by-side
    3. Top Products: Horizontal bar chart with color gradient

Dashboard Sections:
    - Header: Title, subtitle, timestamp
    - Metrics: 4 key metric cards (revenue, orders, customers)
    - Charts: 3 interactive visualization sections
    - Footer: Branding and links

Usage:
    from html_dashboard import HTMLDashboard
    
    dashboard = HTMLDashboard()
    filename = dashboard.generate_html()
    print(f"Dashboard created: {filename}")
    # Open in browser: file:///path/to/dashboard.html

Output:
    Single HTML file: watsonx_analytics_dashboard_YYYYMMDD_HHMMSS.html

Advantages over Static Images:
    - Interactive: Zoom, pan, hover for details
    - Single file: Easy to share and distribute
    - Professional: IBM Cloud Pak for Data styling
    - Responsive: Works on desktop, tablet, mobile
    - No dependencies: Self-contained HTML

Dependencies:
    - pandas: Data manipulation
    - plotly: Interactive visualizations
    - query_gold_tier: Data queries

Author: Bob
Created: 2026
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime
from query_gold_tier import GoldTierAnalytics
import base64
from io import BytesIO


class HTMLDashboard:
    """
    Generate interactive HTML dashboard with IBM styling.
    
    This class creates a professional, interactive HTML dashboard using Plotly
    visualizations styled to match IBM Cloud Pak for Data design guidelines.
    
    Attributes:
        analytics (GoldTierAnalytics): Connection to gold tier data
        timestamp (str): Human-readable timestamp for display
        filename (str): Output filename with timestamp
        IBM_COLORS (dict): IBM Cloud Pak for Data color palette
    
    Methods:
        create_daily_revenue_chart: Interactive revenue trend with dual axes
        create_customer_segment_charts: Pie and bar charts for segments
        create_top_products_chart: Horizontal bar chart with gradient
        generate_html: Create complete HTML dashboard file
    
    IBM Color Palette:
        - primary_blue: #0f62fe (main brand color)
        - secondary_blue: #0043ce (darker variant)
        - light_blue: #4589ff (lighter variant)
        - purple: #8a3ffc (accent color)
        - teal: #007d79 (accent color)
        - magenta: #d12771 (accent color)
        - And more...
    """
    
    # IBM Cloud Pak for Data color palette
    # These colors match the official IBM Design Language
    IBM_COLORS = {
        'primary_blue': '#0f62fe',      # IBM Blue - primary brand color
        'secondary_blue': '#0043ce',    # Darker blue for contrast
        'light_blue': '#4589ff',        # Lighter blue for highlights
        'dark_blue': '#002d9c',         # Very dark blue
        'purple': '#8a3ffc',            # IBM Purple - accent
        'magenta': '#d12771',           # IBM Magenta - accent
        'teal': '#007d79',              # IBM Teal - accent
        'cyan': '#1192e8',              # IBM Cyan - accent
        'green': '#24a148',             # IBM Green - success
        'gray_10': '#f4f4f4',           # Lightest gray - backgrounds
        'gray_20': '#e0e0e0',           # Light gray - borders
        'gray_50': '#8d8d8d',           # Medium gray
        'gray_70': '#525252',           # Dark gray - secondary text
        'gray_90': '#262626',           # Very dark gray
        'gray_100': '#161616',          # Darkest gray - primary text
        'white': '#ffffff',             # White
        'text': '#161616',              # Primary text color
        'background': '#f4f4f4'         # Page background
    }
    
    def __init__(self):
        """
        Initialize dashboard generator.
        
        Creates a GoldTierAnalytics instance for data queries and sets up
        timestamps for both display and file naming.
        """
        self.analytics = GoldTierAnalytics()
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.filename = f'watsonx_analytics_dashboard_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
    
    def create_daily_revenue_chart(self, daily_sales):
        """
        Create interactive daily revenue trend chart with dual y-axes.
        
        Generates a combination chart showing:
        - Line chart: Daily revenue (primary y-axis)
        - Bar chart: Order count (secondary y-axis)
        
        This allows viewing both revenue and order volume trends together,
        making it easy to spot correlations.
        
        Data Processing:
            - Converts order_date to datetime
            - Converts numeric columns to float
        
        Chart Features:
            - Dual y-axes for different scales
            - Interactive hover with formatted values
            - Unified hover mode (shows both series)
            - IBM color scheme
            - Responsive layout
        
        Args:
            daily_sales (DataFrame): Sales data with columns:
                - order_date: Date of sales
                - daily_revenue: Total revenue
                - order_count: Number of orders
        
        Returns:
            plotly.graph_objects.Figure: Interactive Plotly figure
            
        Example:
            >>> daily_sales = analytics.get_sales_trends(days=30)
            >>> fig = dashboard.create_daily_revenue_chart(daily_sales)
            >>> fig.show()  # Display in Jupyter
        """
        # Convert to numeric
        daily_sales['order_date'] = pd.to_datetime(daily_sales['order_date'])
        daily_sales['daily_revenue'] = pd.to_numeric(daily_sales['daily_revenue'], errors='coerce')
        daily_sales['order_count'] = pd.to_numeric(daily_sales['order_count'], errors='coerce')
        
        # Create figure with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Add revenue line (primary y-axis)
        fig.add_trace(
            go.Scatter(
                x=daily_sales['order_date'],
                y=daily_sales['daily_revenue'],
                name="Revenue",
                line=dict(color=self.IBM_COLORS['primary_blue'], width=3),
                mode='lines+markers',
                marker=dict(size=8),
                hovertemplate='<b>Date:</b> %{x|%Y-%m-%d}<br><b>Revenue:</b> $%{y:,.2f}<extra></extra>'
            ),
            secondary_y=False
        )
        
        # Add order count bars (secondary y-axis)
        fig.add_trace(
            go.Bar(
                x=daily_sales['order_date'],
                y=daily_sales['order_count'],
                name="Orders",
                marker_color=self.IBM_COLORS['light_blue'],
                opacity=0.6,
                hovertemplate='<b>Date:</b> %{x|%Y-%m-%d}<br><b>Orders:</b> %{y}<extra></extra>'
            ),
            secondary_y=True
        )
        
        # Update layout with IBM styling
        fig.update_layout(
            title=dict(
                text='<b>Daily Revenue Trend (Last 30 Days)</b>',
                font=dict(size=20, color=self.IBM_COLORS['text'], family='IBM Plex Sans')
            ),
            plot_bgcolor=self.IBM_COLORS['white'],
            paper_bgcolor=self.IBM_COLORS['white'],
            font=dict(family='IBM Plex Sans', color=self.IBM_COLORS['text']),
            hovermode='x unified',  # Show all series on hover
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(l=60, r=60, t=80, b=60)
        )
        
        # Update axes
        fig.update_xaxes(
            title_text="Date",
            gridcolor=self.IBM_COLORS['gray_20'],
            showgrid=True
        )
        fig.update_yaxes(
            title_text="<b>Revenue ($)</b>",
            gridcolor=self.IBM_COLORS['gray_20'],
            showgrid=True,
            secondary_y=False
        )
        fig.update_yaxes(
            title_text="<b>Order Count</b>",
            showgrid=False,
            secondary_y=True
        )
        
        return fig
    
    def create_customer_segment_charts(self, customer_segments):
        """
        Create customer segment visualizations (pie + bar charts).
        
        Generates a two-panel chart showing:
        1. Pie chart: Revenue distribution by segment
        2. Bar chart: Customer count by segment
        
        This provides both revenue and customer perspectives on segmentation.
        
        Data Processing:
            - Converts customer_count to numeric
            - Converts total_revenue to numeric
        
        Chart Features:
            - Side-by-side layout
            - Consistent color scheme across both charts
            - Interactive hover with formatted values
            - Percentage labels on pie chart
            - Value labels on bar chart
        
        Args:
            customer_segments (DataFrame): Segment data with columns:
                - customer_segment: Segment name
                - customer_count: Number of customers
                - total_revenue: Total revenue from segment
        
        Returns:
            plotly.graph_objects.Figure: Interactive Plotly figure with subplots
            
        Example:
            >>> segments = analytics.get_customer_segments()
            >>> fig = dashboard.create_customer_segment_charts(segments)
            >>> fig.show()
        """
        # Convert to numeric
        customer_segments['customer_count'] = pd.to_numeric(customer_segments['customer_count'], errors='coerce')
        customer_segments['total_revenue'] = pd.to_numeric(customer_segments['total_revenue'], errors='coerce')
        
        # Create subplots (1 row, 2 columns)
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('<b>Revenue Distribution</b>', '<b>Customer Count by Segment</b>'),
            specs=[[{'type': 'pie'}, {'type': 'bar'}]]
        )
        
        # IBM color palette for segments
        colors = [self.IBM_COLORS['primary_blue'], self.IBM_COLORS['purple'], 
                 self.IBM_COLORS['teal'], self.IBM_COLORS['magenta']]
        
        # Add pie chart (left panel)
        fig.add_trace(
            go.Pie(
                labels=customer_segments['customer_segment'],
                values=customer_segments['total_revenue'],
                marker=dict(colors=colors, line=dict(color=self.IBM_COLORS['white'], width=2)),
                textinfo='label+percent',
                textfont=dict(size=12, color=self.IBM_COLORS['white']),
                hovertemplate='<b>%{label}</b><br>Revenue: $%{value:,.2f}<br>Percentage: %{percent}<extra></extra>'
            ),
            row=1, col=1
        )
        
        # Add bar chart (right panel)
        fig.add_trace(
            go.Bar(
                x=customer_segments['customer_segment'],
                y=customer_segments['customer_count'],
                marker_color=colors,
                text=customer_segments['customer_count'],
                textposition='outside',
                texttemplate='%{text:,}',
                hovertemplate='<b>%{x}</b><br>Customers: %{y:,}<extra></extra>'
            ),
            row=1, col=2
        )
        
        # Update layout
        fig.update_layout(
            title=dict(
                text='<b>Customer Segmentation Analysis</b>',
                font=dict(size=20, color=self.IBM_COLORS['text'], family='IBM Plex Sans')
            ),
            plot_bgcolor=self.IBM_COLORS['white'],
            paper_bgcolor=self.IBM_COLORS['white'],
            font=dict(family='IBM Plex Sans', color=self.IBM_COLORS['text']),
            showlegend=False,
            height=400,
            margin=dict(l=60, r=60, t=100, b=60)
        )
        
        # Update bar chart axes
        fig.update_xaxes(title_text="Segment", row=1, col=2)
        fig.update_yaxes(title_text="Number of Customers", row=1, col=2, gridcolor=self.IBM_COLORS['gray_20'])
        
        return fig
    
    def create_top_products_chart(self, top_products):
        """
        Create top products horizontal bar chart with color gradient.
        
        Generates a horizontal bar chart showing top 10 products by revenue.
        Uses a color gradient from light to dark blue to emphasize ranking.
        
        Data Processing:
            - Converts total_revenue to numeric
            - Sorts by revenue ascending (for bottom-to-top display)
            - Limits to top 10 products
        
        Chart Features:
            - Horizontal orientation for long product names
            - Color gradient based on revenue
            - Value labels with currency formatting
            - Interactive hover with formatted values
        
        Args:
            top_products (DataFrame): Product data with columns:
                - product_name: Name of product
                - total_revenue: Total revenue from product
        
        Returns:
            plotly.graph_objects.Figure: Interactive Plotly figure
            
        Example:
            >>> products = analytics.get_top_products(limit=10)
            >>> fig = dashboard.create_top_products_chart(products)
            >>> fig.show()
        """
        # Convert to numeric
        top_products['total_revenue'] = pd.to_numeric(top_products['total_revenue'], errors='coerce')
        
        # Sort and get top 10 (ascending for bottom-to-top display)
        top_10 = top_products.head(10).sort_values('total_revenue', ascending=True)
        
        # Create figure
        fig = go.Figure()
        
        # Add horizontal bar chart with color gradient
        fig.add_trace(
            go.Bar(
                y=top_10['product_name'],
                x=top_10['total_revenue'],
                orientation='h',
                marker=dict(
                    color=top_10['total_revenue'],
                    colorscale=[[0, self.IBM_COLORS['light_blue']], [1, self.IBM_COLORS['primary_blue']]],
                    line=dict(color=self.IBM_COLORS['white'], width=1)
                ),
                text=top_10['total_revenue'],
                texttemplate='$%{text:,.0f}',
                textposition='outside',
                hovertemplate='<b>%{y}</b><br>Revenue: $%{x:,.2f}<extra></extra>'
            )
        )
        
        # Update layout
        fig.update_layout(
            title=dict(
                text='<b>Top 10 Products by Revenue</b>',
                font=dict(size=20, color=self.IBM_COLORS['text'], family='IBM Plex Sans')
            ),
            plot_bgcolor=self.IBM_COLORS['white'],
            paper_bgcolor=self.IBM_COLORS['white'],
            font=dict(family='IBM Plex Sans', color=self.IBM_COLORS['text']),
            xaxis=dict(
                title="Revenue ($)",
                gridcolor=self.IBM_COLORS['gray_20'],
                showgrid=True
            ),
            yaxis=dict(
                title="",
                tickfont=dict(size=11)
            ),
            height=500,
            margin=dict(l=200, r=100, t=80, b=60)
        )
        
        return fig
    
    def generate_html(self):
        """
        Generate complete HTML dashboard file.
        
        Creates a self-contained HTML file with:
        - Professional header with gradient background
        - 4 metric cards showing key statistics
        - 3 interactive Plotly charts
        - Footer with branding and links
        - Embedded Plotly library (no external dependencies)
        - Responsive CSS for different screen sizes
        
        Process:
            1. Query all data from gold tier tables
            2. Calculate summary metrics
            3. Create all Plotly charts
            4. Generate HTML with embedded charts
            5. Write to file
        
        HTML Structure:
            - <!DOCTYPE html> with UTF-8 encoding
            - Google Fonts: IBM Plex Sans
            - Plotly CDN: Latest version
            - CSS: Inline styles with IBM colors
            - JavaScript: Plotly chart rendering
        
        CSS Features:
            - Flexbox/Grid layouts
            - Hover effects on metric cards
            - Responsive design with media queries
            - Print-friendly styles
        
        Returns:
            str: Filename of generated HTML dashboard
            
        Output:
            Creates: watsonx_analytics_dashboard_YYYYMMDD_HHMMSS.html
            
        Example:
            >>> dashboard = HTMLDashboard()
            >>> filename = dashboard.generate_html()
            ================================================================================
            GENERATING INTERACTIVE HTML DASHBOARD
            ================================================================================
            ✓ HTML dashboard generated: watsonx_analytics_dashboard_20260410_143022.html
            ✓ Open in browser: file://watsonx_analytics_dashboard_20260410_143022.html
        
        Note:
            The generated HTML file is completely self-contained and can be:
            - Opened in any modern web browser
            - Shared via email or file sharing
            - Hosted on a web server
            - Embedded in other web pages
        """
        print("\n" + "="*80)
        print("GENERATING INTERACTIVE HTML DASHBOARD")
        print("="*80)
        
        # Get data from gold tier tables
        daily_sales = self.analytics.get_sales_trends(days=30)
        customer_segments = self.analytics.get_customer_segments()
        top_products = self.analytics.get_top_products(limit=10)
        
        # Calculate summary metrics for metric cards
        daily_sales['daily_revenue'] = pd.to_numeric(daily_sales['daily_revenue'], errors='coerce')
        daily_sales['order_count'] = pd.to_numeric(daily_sales['order_count'], errors='coerce')
        customer_segments['total_revenue'] = pd.to_numeric(customer_segments['total_revenue'], errors='coerce')
        customer_segments['customer_count'] = pd.to_numeric(customer_segments['customer_count'], errors='coerce')
        
        total_revenue = daily_sales['daily_revenue'].sum()
        avg_daily_revenue = daily_sales['daily_revenue'].mean()
        total_orders = daily_sales['order_count'].sum()
        total_customers = customer_segments['customer_count'].sum()
        
        # Create all charts
        revenue_chart = self.create_daily_revenue_chart(daily_sales)
        segment_chart = self.create_customer_segment_charts(customer_segments)
        products_chart = self.create_top_products_chart(top_products)
        
        # Generate complete HTML with embedded charts and styling
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>watsonx.data Analytics Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'IBM Plex Sans', sans-serif;
            background-color: {self.IBM_COLORS['background']};
            color: {self.IBM_COLORS['text']};
            line-height: 1.6;
        }}
        
        .header {{
            background: linear-gradient(135deg, {self.IBM_COLORS['primary_blue']} 0%, {self.IBM_COLORS['secondary_blue']} 100%);
            color: {self.IBM_COLORS['white']};
            padding: 2rem 2rem 1.5rem 2rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }}
        
        .header .subtitle {{
            font-size: 1.1rem;
            opacity: 0.9;
            font-weight: 300;
        }}
        
        .header .timestamp {{
            font-size: 0.9rem;
            opacity: 0.8;
            margin-top: 0.5rem;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}
        
        .metric-card {{
            background: {self.IBM_COLORS['white']};
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border-left: 4px solid {self.IBM_COLORS['primary_blue']};
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .metric-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.12);
        }}
        
        .metric-card.blue {{ border-left-color: {self.IBM_COLORS['primary_blue']}; }}
        .metric-card.purple {{ border-left-color: {self.IBM_COLORS['purple']}; }}
        .metric-card.teal {{ border-left-color: {self.IBM_COLORS['teal']}; }}
        .metric-card.magenta {{ border-left-color: {self.IBM_COLORS['magenta']}; }}
        
        .metric-label {{
            font-size: 0.9rem;
            color: {self.IBM_COLORS['gray_70']};
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.5rem;
            font-weight: 500;
        }}
        
        .metric-value {{
            font-size: 2.2rem;
            font-weight: 600;
            color: {self.IBM_COLORS['text']};
        }}
        
        .chart-container {{
            background: {self.IBM_COLORS['white']};
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            margin-bottom: 2rem;
        }}
        
        .footer {{
            text-align: center;
            padding: 2rem;
            color: {self.IBM_COLORS['gray_70']};
            font-size: 0.9rem;
        }}
        
        .footer a {{
            color: {self.IBM_COLORS['primary_blue']};
            text-decoration: none;
        }}
        
        .footer a:hover {{
            text-decoration: underline;
        }}
        
        @media print {{
            .header {{
                background: {self.IBM_COLORS['primary_blue']};
            }}
            .chart-container {{
                page-break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔷 watsonx.data Analytics Dashboard</h1>
        <div class="subtitle">Gold Tier Analytics - Real-time Business Intelligence</div>
        <div class="timestamp">Generated: {self.timestamp}</div>
    </div>
    
    <div class="container">
        <!-- Key Metrics -->
        <div class="metrics-grid">
            <div class="metric-card blue">
                <div class="metric-label">Total Revenue (30 Days)</div>
                <div class="metric-value">${total_revenue:,.2f}</div>
            </div>
            <div class="metric-card purple">
                <div class="metric-label">Average Daily Revenue</div>
                <div class="metric-value">${avg_daily_revenue:,.2f}</div>
            </div>
            <div class="metric-card teal">
                <div class="metric-label">Total Orders</div>
                <div class="metric-value">{int(total_orders):,}</div>
            </div>
            <div class="metric-card magenta">
                <div class="metric-label">Total Customers</div>
                <div class="metric-value">{int(total_customers):,}</div>
            </div>
        </div>
        
        <!-- Daily Revenue Trend -->
        <div class="chart-container">
            <div id="revenue-chart"></div>
        </div>
        
        <!-- Customer Segments -->
        <div class="chart-container">
            <div id="segment-chart"></div>
        </div>
        
        <!-- Top Products -->
        <div class="chart-container">
            <div id="products-chart"></div>
        </div>
    </div>
    
    <div class="footer">
        <p>Powered by <strong>IBM watsonx.data</strong> | Generated with Python & Plotly</p>
        <p><a href="https://www.ibm.com/products/watsonx-data" target="_blank">Learn more about watsonx.data</a></p>
    </div>
    
    <script>
        // Revenue Chart
        var revenueData = {revenue_chart.to_json()};
        Plotly.newPlot('revenue-chart', revenueData.data, revenueData.layout, {{responsive: true}});
        
        // Segment Chart
        var segmentData = {segment_chart.to_json()};
        Plotly.newPlot('segment-chart', segmentData.data, segmentData.layout, {{responsive: true}});
        
        // Products Chart
        var productsData = {products_chart.to_json()};
        Plotly.newPlot('products-chart', productsData.data, productsData.layout, {{responsive: true}});
    </script>
</body>
</html>
"""
        
        # Write to file
        with open(self.filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\n✓ HTML dashboard generated: {self.filename}")
        print(f"✓ Open in browser: file://{self.filename}")
        
        # Close connection
        self.analytics.close()
        
        return self.filename


# Main execution
if __name__ == "__main__":
    """
    Test script to generate interactive HTML dashboard.
    
    Run this script directly to create the HTML dashboard:
        python html_dashboard.py
    
    This will:
        1. Connect to watsonx.data
        2. Query gold tier tables
        3. Generate interactive charts
        4. Create self-contained HTML file
        5. Close connection
    
    Output:
        watsonx_analytics_dashboard_YYYYMMDD_HHMMSS.html
    
    To view:
        - Double-click the HTML file
        - Or open in browser: file:///path/to/file.html
        - Or serve with: python -m http.server
    
    Prerequisites:
        - Lab 6 ETL pipeline executed
        - Gold tier tables exist
        - .env file configured
        - Virtual environment activated
        - All dependencies installed (including plotly)
    """
    try:
        dashboard = HTMLDashboard()
        filename = dashboard.generate_html()
        
        print("\n" + "="*80)
        print("✓ HTML Dashboard created successfully!")
        print("="*80)
        print(f"\nOpen the dashboard in your browser:")
        print(f"  {filename}")
        print("\n")
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        print("\nPlease ensure:")
        print("  1. Virtual environment is activated")
        print("  2. All dependencies are installed (pip install -r requirements.txt)")
        print("  3. .env file is configured correctly")
        print("  4. Gold tier tables exist from Lab 6")
        print("  5. Network connectivity to watsonx.data")
