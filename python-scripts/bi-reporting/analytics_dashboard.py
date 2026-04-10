"""
Analytics Dashboard Module
Create visualizations from gold tier data
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from query_gold_tier import GoldTierAnalytics

# Set style for better-looking plots
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)


class AnalyticsDashboard:
    """
    Create visualizations from gold tier data
    """
    
    def __init__(self):
        """Initialize analytics connection and timestamp"""
        self.analytics = GoldTierAnalytics()
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def create_daily_sales_chart(self):
        """
        Create line chart for daily sales trends
        
        Returns:
            pandas.DataFrame: Sales trend data
        """
        print("\n📊 Creating Daily Sales Trend Chart...")
        
        df = self.analytics.get_sales_trends(days=30)
        
        # Convert order_date to datetime and numeric columns to float
        df['order_date'] = pd.to_datetime(df['order_date'])
        df['daily_revenue'] = pd.to_numeric(df['daily_revenue'], errors='coerce')
        df['order_count'] = pd.to_numeric(df['order_count'], errors='coerce')
        df['avg_order_value'] = pd.to_numeric(df['avg_order_value'], errors='coerce')
        
        # Create figure with subplots
        fig, axes = plt.subplots(2, 1, figsize=(14, 10))
        
        # Plot 1: Daily Revenue
        axes[0].plot(df['order_date'], df['daily_revenue'],
                    marker='o', linewidth=2, markersize=6, color='#2E86AB')
        axes[0].set_title('Daily Revenue Trend', fontsize=16, fontweight='bold')
        axes[0].set_xlabel('Date', fontsize=12)
        axes[0].set_ylabel('Revenue ($)', fontsize=12)
        axes[0].grid(True, alpha=0.3)
        axes[0].tick_params(axis='x', rotation=45)
        
        # Add trend line
        z = np.polyfit(range(len(df)), df['daily_revenue'], 1)
        p = np.poly1d(z)
        axes[0].plot(df['order_date'], p(range(len(df))),
                    "--", color='red', alpha=0.8, label='Trend')
        axes[0].legend()
        
        # Plot 2: Order Count
        axes[1].bar(df['order_date'], df['order_count'],
                   color='#A23B72', alpha=0.7)
        axes[1].set_title('Daily Order Count', fontsize=16, fontweight='bold')
        axes[1].set_xlabel('Date', fontsize=12)
        axes[1].set_ylabel('Number of Orders', fontsize=12)
        axes[1].grid(True, alpha=0.3, axis='y')
        axes[1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        filename = f'daily_sales_trend_{self.timestamp}.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"✓ Saved: {filename}")
        plt.close()
        
        return df
    
    def create_customer_segment_chart(self):
        """
        Create pie chart and bar chart for customer segments
        
        Returns:
            pandas.DataFrame: Customer segment data
        """
        print("\n📊 Creating Customer Segment Charts...")
        
        df = self.analytics.get_customer_segments()
        
        # Convert numeric columns
        df['customer_count'] = pd.to_numeric(df['customer_count'], errors='coerce')
        df['total_revenue'] = pd.to_numeric(df['total_revenue'], errors='coerce')
        
        # Create figure with subplots
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        
        # Plot 1: Pie chart for revenue distribution
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
        explode = [0.05 if i == 0 else 0 for i in range(len(df))]
        
        axes[0].pie(df['total_revenue'], labels=df['customer_segment'], 
                   autopct='%1.1f%%', startangle=90, colors=colors,
                   explode=explode, shadow=True)
        axes[0].set_title('Revenue Distribution by Customer Segment', 
                         fontsize=14, fontweight='bold')
        
        # Plot 2: Bar chart for customer count
        bars = axes[1].bar(df['customer_segment'], df['customer_count'], 
                          color=colors, alpha=0.8)
        axes[1].set_title('Customer Count by Segment', 
                         fontsize=14, fontweight='bold')
        axes[1].set_xlabel('Customer Segment', fontsize=12)
        axes[1].set_ylabel('Number of Customers', fontsize=12)
        axes[1].tick_params(axis='x', rotation=45)
        axes[1].grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            axes[1].text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height):,}',
                        ha='center', va='bottom', fontsize=10)
        
        plt.tight_layout()
        filename = f'customer_segments_{self.timestamp}.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"✓ Saved: {filename}")
        plt.close()
        
        return df
    
    def create_top_products_chart(self):
        """
        Create horizontal bar chart for top products
        
        Returns:
            pandas.DataFrame: Top products data
        """
        print("\n📊 Creating Top Products Chart...")
        
        df = self.analytics.get_top_products(limit=15)
        
        # Convert numeric columns
        df['total_revenue'] = pd.to_numeric(df['total_revenue'], errors='coerce')
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 10))
        
        # Create horizontal bar chart
        bars = ax.barh(df['product_name'], df['total_revenue'], 
                      color='#6C5CE7', alpha=0.8)
        
        ax.set_title('Top 15 Products by Revenue', 
                    fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Total Revenue ($)', fontsize=12)
        ax.set_ylabel('Product Name', fontsize=12)
        ax.grid(True, alpha=0.3, axis='x')
        
        # Add value labels
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2.,
                   f'${width:,.0f}',
                   ha='left', va='center', fontsize=9, 
                   bbox=dict(boxstyle='round,pad=0.3', 
                           facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        filename = f'top_products_{self.timestamp}.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"✓ Saved: {filename}")
        plt.close()
        
        return df
    
    def create_comprehensive_dashboard(self):
        """
        Create a comprehensive dashboard with multiple visualizations
        
        Returns:
            str: Filename of saved dashboard
        """
        print("\n" + "="*80)
        print("CREATING COMPREHENSIVE ANALYTICS DASHBOARD")
        print("="*80)
        
        # Get all data
        daily_sales = self.analytics.get_sales_trends(days=30)
        customer_segments = self.analytics.get_customer_segments()
        top_products = self.analytics.get_top_products(limit=10)
        
        # Convert dates and numeric columns
        daily_sales['order_date'] = pd.to_datetime(daily_sales['order_date'])
        daily_sales['daily_revenue'] = pd.to_numeric(daily_sales['daily_revenue'], errors='coerce')
        daily_sales['order_count'] = pd.to_numeric(daily_sales['order_count'], errors='coerce')
        
        # Convert customer segment numeric columns
        customer_segments['customer_count'] = pd.to_numeric(customer_segments['customer_count'], errors='coerce')
        customer_segments['total_revenue'] = pd.to_numeric(customer_segments['total_revenue'], errors='coerce')
        
        # Convert top products numeric columns
        top_products['total_revenue'] = pd.to_numeric(top_products['total_revenue'], errors='coerce')
        
        # Create comprehensive dashboard with better spacing
        fig = plt.figure(figsize=(22, 14))
        gs = fig.add_gridspec(3, 2, hspace=0.4, wspace=0.35,
                             top=0.93, bottom=0.05, left=0.08, right=0.95)
        
        # 1. Daily Revenue Trend
        ax1 = fig.add_subplot(gs[0, :])
        ax1.plot(daily_sales['order_date'], daily_sales['daily_revenue'],
                marker='o', linewidth=2.5, markersize=6, color='#2E86AB',
                label='Daily Revenue')
        ax1.fill_between(daily_sales['order_date'], daily_sales['daily_revenue'],
                        alpha=0.2, color='#2E86AB')
        ax1.set_title('Daily Revenue Trend (Last 30 Days)',
                     fontsize=18, fontweight='bold', pad=15)
        ax1.set_xlabel('Date', fontsize=13, labelpad=10)
        ax1.set_ylabel('Revenue ($)', fontsize=13, labelpad=10)
        ax1.grid(True, alpha=0.3, linestyle='--')
        ax1.tick_params(axis='x', rotation=45, labelsize=10)
        ax1.tick_params(axis='y', labelsize=10)
        ax1.legend(loc='upper left', fontsize=11)
        
        # Format y-axis as currency
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        # 2. Customer Segments - Pie Chart
        ax2 = fig.add_subplot(gs[1, 0])
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
        wedges, texts, autotexts = ax2.pie(customer_segments['total_revenue'],
               labels=customer_segments['customer_segment'],
               autopct='%1.1f%%', startangle=90, colors=colors,
               shadow=True, explode=[0.05] * len(customer_segments),
               textprops={'fontsize': 11})
        
        # Make percentage text bold and white
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(10)
        
        ax2.set_title('Revenue Distribution by Customer Segment',
                     fontsize=15, fontweight='bold', pad=15)
        
        # 3. Customer Count by Segment
        ax3 = fig.add_subplot(gs[1, 1])
        bars = ax3.bar(customer_segments['customer_segment'],
                      customer_segments['customer_count'],
                      color=colors, alpha=0.85, edgecolor='white', linewidth=1.5)
        ax3.set_title('Customer Count by Segment',
                     fontsize=15, fontweight='bold', pad=15)
        ax3.set_xlabel('Segment', fontsize=12, labelpad=10)
        ax3.set_ylabel('Number of Customers', fontsize=12, labelpad=10)
        ax3.tick_params(axis='x', rotation=45, labelsize=10)
        ax3.tick_params(axis='y', labelsize=10)
        ax3.grid(True, alpha=0.3, axis='y', linestyle='--')
        ax3.set_axisbelow(True)
        
        # Add value labels with better positioning
        for bar in bars:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height + (ax3.get_ylim()[1] * 0.02),
                    f'{int(height):,}',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        # 4. Top Products
        ax4 = fig.add_subplot(gs[2, :])
        top_10 = top_products.head(10)
        bars = ax4.barh(range(len(top_10)), top_10['total_revenue'],
                       color='#6C5CE7', alpha=0.85, edgecolor='white', linewidth=1.5)
        
        # Set product names as y-tick labels
        ax4.set_yticks(range(len(top_10)))
        ax4.set_yticklabels(top_10['product_name'], fontsize=11)
        
        ax4.set_title('Top 10 Products by Revenue',
                     fontsize=15, fontweight='bold', pad=15)
        ax4.set_xlabel('Revenue ($)', fontsize=12, labelpad=10)
        ax4.grid(True, alpha=0.3, axis='x', linestyle='--')
        ax4.set_axisbelow(True)
        ax4.tick_params(axis='x', labelsize=10)
        
        # Format x-axis as currency
        ax4.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        # Add value labels with better positioning
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax4.text(width + (ax4.get_xlim()[1] * 0.01), bar.get_y() + bar.get_height()/2.,
                    f'${width:,.0f}',
                    ha='left', va='center', fontsize=10, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.4',
                            facecolor='white', edgecolor='gray', alpha=0.9))
        
        # Add main title with better positioning
        fig.suptitle('watsonx.data Analytics Dashboard - Gold Tier Analysis',
                    fontsize=22, fontweight='bold', y=0.98)
        
        # Save dashboard
        filename = f'comprehensive_dashboard_{self.timestamp}.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"\n✓ Comprehensive dashboard saved: {filename}")
        plt.close()
        
        return filename
    
    def generate_summary_report(self):
        """
        Generate a text summary report
        """
        print("\n" + "="*80)
        print("ANALYTICS SUMMARY REPORT")
        print("="*80)
        
        # Get data
        daily_sales = self.analytics.get_sales_trends(days=30)
        customer_segments = self.analytics.get_customer_segments()
        
        # Convert to numeric types
        daily_sales['daily_revenue'] = pd.to_numeric(daily_sales['daily_revenue'], errors='coerce')
        daily_sales['order_count'] = pd.to_numeric(daily_sales['order_count'], errors='coerce')
        
        # Convert customer segments numeric columns
        customer_segments['customer_count'] = pd.to_numeric(customer_segments['customer_count'], errors='coerce')
        customer_segments['total_revenue'] = pd.to_numeric(customer_segments['total_revenue'], errors='coerce')
        customer_segments['revenue_percentage'] = pd.to_numeric(customer_segments['revenue_percentage'], errors='coerce')
        
        # Calculate metrics
        total_revenue = daily_sales['daily_revenue'].sum()
        avg_daily_revenue = daily_sales['daily_revenue'].mean()
        total_orders = daily_sales['order_count'].sum()
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        # Print summary
        print(f"\n📈 SALES METRICS (Last 30 Days)")
        print(f"   Total Revenue: ${total_revenue:,.2f}")
        print(f"   Average Daily Revenue: ${avg_daily_revenue:,.2f}")
        print(f"   Total Orders: {total_orders:,}")
        print(f"   Average Order Value: ${avg_order_value:,.2f}")
        
        print(f"\n👥 CUSTOMER SEGMENTS")
        for _, row in customer_segments.iterrows():
            print(f"   {row['customer_segment']}: "
                  f"{int(row['customer_count']):,} customers, "
                  f"${float(row['total_revenue']):,.2f} revenue "
                  f"({float(row['revenue_percentage']):.1f}%)")
        
        print("\n" + "="*80)
    
    def run_complete_analysis(self):
        """
        Run complete analysis workflow
        """
        print("\n" + "="*80)
        print("STARTING COMPLETE ANALYTICS WORKFLOW")
        print("="*80)
        
        # Generate individual charts
        self.create_daily_sales_chart()
        self.create_customer_segment_chart()
        self.create_top_products_chart()
        
        # Generate comprehensive dashboard
        dashboard_file = self.create_comprehensive_dashboard()
        
        # Generate summary report
        self.generate_summary_report()
        
        print("\n" + "="*80)
        print("✓ ANALYTICS WORKFLOW COMPLETED")
        print("="*80)
        print(f"\nGenerated Files:")
        print(f"  - daily_sales_trend_{self.timestamp}.png")
        print(f"  - customer_segments_{self.timestamp}.png")
        print(f"  - top_products_{self.timestamp}.png")
        print(f"  - {dashboard_file}")
        print("\n")
        
        # Close connection
        self.analytics.close()


# Main execution
if __name__ == "__main__":
    try:
        dashboard = AnalyticsDashboard()
        dashboard.run_complete_analysis()
        
        print("="*80)
        print("✓ All visualizations created successfully!")
        print("="*80)
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        print("\nPlease ensure:")
        print("  1. Virtual environment is activated")
        print("  2. All dependencies are installed")
        print("  3. .env file is configured correctly")
        print("  4. Gold tier tables exist from Lab 6")

# Made with Bob
