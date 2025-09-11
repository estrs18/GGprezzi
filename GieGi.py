import gradio as gr
import pandas as pd
from io import BytesIO
import re

def load_excel(file, file_type):
    """
    Load Excel file and return a dataframe with sheet information
    """
    try:
        # Read all sheets
        sheets = pd.read_excel(file.name, sheet_name=None)
        
        # Create HTML for displaying all sheets
        html_content = f"<h2>{file_type} File: {file.name}</h2>"
        
        for sheet_name, df in sheets.items():
            # Remove empty columns
            df = df.dropna(axis=1, how='all')
            # Remove empty rows
            df = df.dropna(axis=0, how='all')
            
            # Check if dataframe is empty after cleaning
            if df.empty:
                html_content += f"<h3>Sheet: {sheet_name}</h3><p>No data available after cleaning</p>"
                continue
                
            html_content += f"<h3>Sheet: {sheet_name}</h3>"
            html_content += df.to_html(index=False, table_id=f"{file_type}_{sheet_name}")
            
        return html_content, sheets  # Return both HTML and raw data  
    except Exception as e:
        return f"Error loading file: {str(e)}", None

def search_tuples(sheets, search_tuple_str, file_type):
    """
    Search for rows containing the specified tuple values and display only first and tenth columns
    """
    if not sheets:
        return "No data to search"
    
    try:
        # Parse the search tuple from string
        search_values = [val.strip() for val in search_tuple_str.split(',') if val.strip()]
        
        if not search_values:
            return "No search values provided"
        
        results = []
        
        for sheet_name, df in sheets.items():
            # Remove empty columns and rows
            df = df.dropna(axis=1, how='all')
            df = df.dropna(axis=0, how='all')
            
            if df.empty:
                continue
                
            # Search for rows containing all search values
            matching_rows = []
            for idx, row in df.iterrows():
                # Convert row to list of string values for comparison
                row_values = [str(val) if pd.notna(val) else '' for val in row]
                # Check if all search values are found in the row (case-insensitive)
                found_all = all(any(search_val.lower() in row_val.lower() 
                                  for row_val in row_values) 
                              for search_val in search_values)
                
                if found_all:
                    matching_rows.append({
                        'row_index': idx,
                        'values': list(row),
                        'sheet': sheet_name,
                        'file_type': file_type
                    })
            
            if matching_rows:
                results.append({
                    'sheet': sheet_name,
                    'rows': matching_rows
                })
        
        if not results:
            return "No rows found matching the search criteria"
        
        # Generate HTML for results
        html_output = f"<h3> Risultati Ricerca {file_type} [Nome prodotto | costo in euro al metro] </h3>"
        for result in results:
            html_output += f"<h4>Sheet: {result['sheet']}</h4>"
            for row_info in result['rows']:
                # Get first and tenth columns (or last column if fewer than 10)
                values = row_info['values']
                num_cols = len(values)
                
                # Determine indices to show
                col_indices = [0]  # Always include first column
                if num_cols >= 10:
                    col_indices.append(9)  # Tenth column (index 9)
                else:
                    col_indices.append(num_cols - 1)  # Last column
                
                # Extract selected columns
                selected_values = [values[i] for i in col_indices]
                
                html_output += f"<p><b>Row {row_info['row_index']}:</b></p>"
                html_output += "<table border='1' style='border-collapse: collapse;'>"
                html_output += "<tr>"
                for val in selected_values:
                    html_output += f"<td style='border: 1px solid #ddd; padding: 8px;'>{val}</td>"
                html_output += "</tr></table><br>"
        
        return html_output
        
    except Exception as e:
        return f"Error during search: {str(e)}"

def search_in_excel(inventario_file, search_tuple_str):
    """
    Main function to handle file uploads and search for both files
    """
    # Load inventario file
    if inventario_file:
        inventario_html, inventario_sheets = load_excel(inventario_file, "Inventario")
    else:
        inventario_html, inventario_sheets = "<h2>No Inventario file uploaded</h2>", None
    
    # Perform search only on inventario
    if inventario_sheets and search_tuple_str:
        inventario_search = search_tuples(inventario_sheets, search_tuple_str, "Inventario")
    else:
        inventario_search = ""
    
    return inventario_search

# Create Gradio interface
with gr.Blocks() as demo:
    gr.Markdown("# Excel Spreadsheet Viewer with Tuple Search")
    gr.Markdown("Upload Excel files for Inventario and QCC to view their contents and search for specific values")
    
    # File upload components
    with gr.Row():
        inventario_file = gr.File(label="Upload Inventario Excel File", file_types=[".xlsx", ".xls"])
        qcc_file = gr.File(label="Upload QCC Excel File", file_types=[".xlsx", ".xls"])
    
    # Search tuple input
    search_tuple_input = gr.Textbox(
        label="Search Tuple Values (comma separated)",
        placeholder="Enter values to search for, e.g.: 'John,Smith,25'"
    )
    
    # Output components
    excel_output = gr.HTML(label="Excel Data")
    search_output = gr.HTML(label="Search Results")
    
    # Search button
    search_button = gr.Button("Search for Tuple Values")
    
    # Event handling
    inventario_file.change(
        fn=lambda f: load_excel(f, "Inventario")[0] if f else "<h2>No Inventario file uploaded</h2>",
        inputs=inventario_file,
        #outputs=excel_output commented in order to avoid showing the file
    )
    
    qcc_file.change(
        fn=lambda f: load_excel(f, "QCC")[0] if f else "<h2>No QCC file uploaded</h2>",
        inputs=qcc_file,
        #outputs=excel_output commented in order to avoid showing the file
    )
    
    # Search button click
    search_button.click(
        fn=search_in_excel,
        inputs=[inventario_file, search_tuple_input],
        outputs=[search_output]
    )

# Launch the app
if __name__ == "__main__":
    demo.launch()

