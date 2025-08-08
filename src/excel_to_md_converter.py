#!/usr/bin/env python3
"""
Excel to Markdown Converter
Converts multiple Excel files from data/ directory into a combined markdown file
"""

import pandas as pd
import os
from pathlib import Path
import logging

class ExcelToMarkdownConverter:
    """Handles conversion of Excel files to combined Markdown format"""
    
    def __init__(self, data_dir="data", output_file="combined_data.md"):
        """
        Initialize converter
        
        Args:
            data_dir (str): Directory containing Excel files
            output_file (str): Output markdown file path
        """
        self.data_dir = Path(data_dir)
        self.output_file = output_file
        self.logger = logging.getLogger(__name__)
        
    def find_excel_files(self):
        """Find all Excel files in data directory"""
        excel_extensions = ['.xlsx', '.xls']
        excel_files = []
        
        if not self.data_dir.exists():
            self.logger.warning(f"Data directory {self.data_dir} does not exist")
            return excel_files
            
        for ext in excel_extensions:
            excel_files.extend(self.data_dir.glob(f'*{ext}'))
            
        return excel_files
    
    def excel_to_markdown_table(self, df, sheet_name="Sheet"):
        """
        Convert DataFrame to Markdown table format
        
        Args:
            df (pd.DataFrame): DataFrame to convert
            sheet_name (str): Name of the sheet
            
        Returns:
            str: Markdown formatted table
        """
        # Handle case where data is stored as column headers (0 rows, many columns)
        if len(df) == 0 and len(df.columns) > 0:
            # Data is stored as column headers, convert to list format
            markdown_content = f"\n### {sheet_name}\n\n"
            markdown_content += "**Data entries:**\n\n"
            
            for i, col in enumerate(df.columns, 1):
                # Clean and format each entry
                entry = str(col).strip()
                markdown_content += f"{i}. {entry}\n"
            
            markdown_content += "\n"
            return markdown_content
        
        # Regular case with actual data rows
        if df.empty:
            return f"\n### {sheet_name}\n\n*No data found in this sheet*\n\n"
        
        # Clean column names
        df.columns = [str(col).strip() for col in df.columns]
        
        # Convert to markdown table
        markdown_content = f"\n### {sheet_name}\n\n"
        
        # Create table headers
        headers = "| " + " | ".join(df.columns) + " |\n"
        separator = "|" + "|".join([" --- " for _ in df.columns]) + "|\n"
        
        markdown_content += headers + separator
        
        # Add data rows
        for _, row in df.iterrows():
            row_data = []
            for value in row:
                # Handle NaN values and convert to string
                if pd.isna(value):
                    row_data.append("")
                else:
                    # Escape pipe characters in cell content
                    cell_content = str(value).replace("|", "\\|").replace("\n", " ")
                    row_data.append(cell_content)
            
            markdown_content += "| " + " | ".join(row_data) + " |\n"
        
        markdown_content += "\n"
        return markdown_content
    
    def process_excel_file(self, file_path):
        """
        Process a single Excel file and convert to Markdown
        
        Args:
            file_path (Path): Path to Excel file
            
        Returns:
            str: Markdown content from the file
        """
        try:
            # Read Excel file with all sheets
            excel_data = pd.read_excel(file_path, sheet_name=None, engine='openpyxl')
            
            file_markdown = f"\n## {file_path.name}\n\n"
            file_markdown += f"*Source: {file_path}*\n\n"
            
            # Process each sheet
            for sheet_name, df in excel_data.items():
                file_markdown += self.excel_to_markdown_table(df, sheet_name)
            
            return file_markdown
            
        except Exception as e:
            self.logger.error(f"Error processing {file_path}: {str(e)}")
            return f"\n## {file_path.name}\n\n*Error reading file: {str(e)}*\n\n"
    
    def convert_all_files(self):
        """
        Convert all Excel files to a combined Markdown file
        
        Returns:
            bool: Success status
        """
        try:
            # Find all Excel files
            excel_files = self.find_excel_files()
            
            if not excel_files:
                self.logger.warning("No Excel files found in data directory")
                return False
            
            # Initialize markdown content
            markdown_content = "# Combined Data from Excel Files\n\n"
            markdown_content += f"*Generated from {len(excel_files)} Excel file(s)*\n\n"
            markdown_content += "---\n"
            
            # Process each Excel file
            for file_path in excel_files:
                self.logger.info(f"Processing: {file_path}")
                file_content = self.process_excel_file(file_path)
                markdown_content += file_content + "\n---\n"
            
            # Write combined markdown file
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            self.logger.info(f"Successfully created combined markdown file: {self.output_file}")
            print(f"✅ Created {self.output_file} from {len(excel_files)} Excel files")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in conversion process: {str(e)}")
            print(f"❌ Error: {str(e)}")
            return False

def main():
    """Main function to run the converter"""
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize and run converter
    converter = ExcelToMarkdownConverter()
    success = converter.convert_all_files()
    
    if success:
        print("Excel to Markdown conversion completed successfully!")
    else:
        print("Excel to Markdown conversion failed!")
    
    return success

if __name__ == "__main__":
    main()