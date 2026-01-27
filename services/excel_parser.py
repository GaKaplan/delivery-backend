import openpyxl
import re

def parse_excel(file_path, start_row, address_col):
    """
    Parses an Excel file to extract addresses.
    start_row: 1-based index (e.g., 16)
    address_col: Column letter (e.g., 'B')
    """
    extracted_data = []
    
    try:
        workbook = openpyxl.load_workbook(file_path, data_only=True)
        sheet = workbook.active # Assume first sheet
        
        # Convert Column Letter to Index (A=1, B=2...)
        # openpyxl uses 1-based indexing for rows and columns
        from openpyxl.utils import column_index_from_string
        try:
            col_idx = column_index_from_string(address_col)
        except ValueError:
            print(f"Invalid column letter: {address_col}")
            return []

        # Iterate rows
        # openpyxl rows are 1-based.
        # min_row = start_row
        
        for row in sheet.iter_rows(min_row=start_row, min_col=col_idx, max_col=col_idx):
            cell = row[0] 
            if cell.value:
                val = str(cell.value).strip()
                if val:
                    # Basic cleanup if needed, but Excel cells are usually cleaner than PDF lines
                    extracted_data.append({
                        "name": f"Cliente {len(extracted_data)+1}", 
                        "address": val
                    })
                    
        return extracted_data
        
    except Exception as e:
        print(f"Error parsing Excel: {e}")
        return []
