"""
HTML Dashboard Generator for watsonx.data Analytics
Creates an interactive HTML dashboard with IBM Cloud Pak for Data styling
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
    Generate interactive HTML dashboard with IBM styling
    """
    
    # IBM Cloud Pak for Data color palette
    IBM_COLORS = {
        'primary_blue': '#0f62fe',
        'secondary_blue': '#0043ce',
        'light_blue': '#4589ff',
        'dark_blue': '#002d9c',
        'purple': '#8a3ffc',
        'magenta': '#d12771',
        'teal': '#007d79',
        'cyan': '#1192e8',
        'green': '#24a148',
        'gray_10': '#f4f4f4',
        'gray_20': '#e0e0e0',
        'gray_50': '#8d8d8d',
        'gray_70': '#525252',
        'gray_90': '#262626',
        'gray_100': '#161616',
        'white': '#ffffff',
        'text': '#161616',
        'background': '#f4f4f4'
    }
    
    def __init__(self):
        """Initialize dashboard generator"""
        self.analytics = GoldTierAnalytics()
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.filename = f'watsonx_analytics_dashboard_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
    
    def create_daily_revenue_chart(self, daily_sales):
        """Create interactive daily revenue trend chart"""
        # Convert to numeric
        daily_sales['order_date'] = pd.to_datetime(daily_sales['order_date'])
        daily_sales['daily_revenue'] = pd.to_numeric(daily_sales['daily_revenue'], errors='coerce')
        daily_sales['order_count'] = pd.to_numeric(daily_sales['order_count'], errors='coerce')
        
        # Create figure with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Add revenue line
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
        
        # Add order count bars
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
        
        # Update layout
        fig.update_layout(
            title=dict(
                text='<b>Daily Revenue Trend (Last 30 Days)</b>',
                font=dict(size=20, color=self.IBM_COLORS['text'], family='IBM Plex Sans')
            ),
            plot_bgcolor=self.IBM_COLORS['white'],
            paper_bgcolor=self.IBM_COLORS['white'],
            font=dict(family='IBM Plex Sans', color=self.IBM_COLORS['text']),
            hovermode='x unified',
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
        """Create customer segment visualizations"""
        # Convert to numeric
        customer_segments['customer_count'] = pd.to_numeric(customer_segments['customer_count'], errors='coerce')
        customer_segments['total_revenue'] = pd.to_numeric(customer_segments['total_revenue'], errors='coerce')
        
        # Create subplots
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('<b>Revenue Distribution</b>', '<b>Customer Count by Segment</b>'),
            specs=[[{'type': 'pie'}, {'type': 'bar'}]]
        )
        
        # Pie chart colors
        colors = [self.IBM_COLORS['primary_blue'], self.IBM_COLORS['purple'], 
                 self.IBM_COLORS['teal'], self.IBM_COLORS['magenta']]
        
        # Add pie chart
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
        
        # Add bar chart
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
        """Create top products horizontal bar chart"""
        # Convert to numeric
        top_products['total_revenue'] = pd.to_numeric(top_products['total_revenue'], errors='coerce')
        
        # Sort and get top 10
        top_10 = top_products.head(10).sort_values('total_revenue', ascending=True)
        
        # Create figure
        fig = go.Figure()
        
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
        """Generate complete HTML dashboard"""
        print("\n" + "="*80)
        print("GENERATING INTERACTIVE HTML DASHBOARD")
        print("="*80)
        
        # Get data
        daily_sales = self.analytics.get_sales_trends(days=30)
        customer_segments = self.analytics.get_customer_segments()
        top_products = self.analytics.get_top_products(limit=10)
        
        # Calculate summary metrics
        daily_sales['daily_revenue'] = pd.to_numeric(daily_sales['daily_revenue'], errors='coerce')
        daily_sales['order_count'] = pd.to_numeric(daily_sales['order_count'], errors='coerce')
        customer_segments['total_revenue'] = pd.to_numeric(customer_segments['total_revenue'], errors='coerce')
        customer_segments['customer_count'] = pd.to_numeric(customer_segments['customer_count'], errors='coerce')
        
        total_revenue = daily_sales['daily_revenue'].sum()
        avg_daily_revenue = daily_sales['daily_revenue'].mean()
        total_orders = daily_sales['order_count'].sum()
        total_customers = customer_segments['customer_count'].sum()
        
        # Create charts
        revenue_chart = self.create_daily_revenue_chart(daily_sales)
        segment_chart = self.create_customer_segment_charts(customer_segments)
        products_chart = self.create_top_products_chart(top_products)
        
        # Generate HTML
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
        print("  2. All dependencies are installed")
        print("  3. .env file is configured correctly")
        print("  4. Gold tier tables exist from Lab 6")

# Made with Bob
