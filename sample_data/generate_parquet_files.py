#!/usr/bin/env python3
"""
Generate Parquet files from CSV sample data
This script converts CSV files to Parquet format for use in watsonx.data labs
"""

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path
import sys

def convert_csv_to_parquet(csv_file, parquet_file):
    """Convert a CSV file to Parquet format"""
    try:
        print(f"Converting {csv_file} to {parquet_file}...")
        
        # Read CSV file
        df = pd.read_csv(csv_file)
        
        # Convert to PyArrow Table
        table = pa.Table.from_pandas(df)
        
        # Write to Parquet with compression
        pq.write_table(
            table, 
            parquet_file,
            compression='snappy',
            use_dictionary=True,
            write_statistics=True
        )
        
        print(f"✓ Successfully created {parquet_file}")
        print(f"  Rows: {len(df)}, Columns: {len(df.columns)}")
        return True
        
    except Exception as e:
        print(f"✗ Error converting {csv_file}: {str(e)}")
        return False

def main():
    """Main function to convert all CSV files to Parquet"""
    
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    
    # Define CSV files to convert
    csv_files = [
        'customers.csv',
        'orders.csv',
        'products.csv',
        'sales_transactions.csv',
        'external_sales.csv',
        'csv_imports.csv'
    ]
    
    print("=" * 60)
    print("CSV to Parquet Conversion Tool")
    print("=" * 60)
    print()
    
    success_count = 0
    total_count = len(csv_files)
    
    for csv_file in csv_files:
        csv_path = script_dir / csv_file
        parquet_file = csv_file.replace('.csv', '.parquet')
        parquet_path = script_dir / parquet_file
        
        if not csv_path.exists():
            print(f"✗ CSV file not found: {csv_path}")
            continue
            
        if convert_csv_to_parquet(csv_path, parquet_path):
            success_count += 1
        print()
    
    print("=" * 60)
    print(f"Conversion Summary: {success_count}/{total_count} files converted successfully")
    print("=" * 60)
    
    if success_count == total_count:
        print("\n✓ All files converted successfully!")
        return 0
    else:
        print(f"\n✗ {total_count - success_count} file(s) failed to convert")
        return 1

if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
