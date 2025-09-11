import gradio as gr
import pandas as pd
from io import BytesIO
import re

# === CONFIG LOADING ===
def load_config(config_path="config.txt"):
    config = {}
    try:
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    except FileNotFoundError:
        print(f"Config file {config_path} not found. Using defaults.")
    except Exception as e:
        print(f"Error reading config: {e}")
    
    # Default values
    config.setdefault('tempo1', 'Default Value 1')
    config.setdefault('tempo2', 'Default Value 2')
    config.setdefault('tempo3', 'Default Value 3')

    return config

# Load config at startup
config = load_config()

# === FILE HANDLING ===
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
        
        # Generate HTML for results with checkboxes
        html_output = f"<h3>{file_type} Search Results</h3>"
        for result in results:
            html_output += f"<h4>Sheet: {result['sheet']}</h4>"
            for i, row_info in enumerate(result['rows']):
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
                
                # Create unique ID for checkbox
                checkbox_id = f"checkbox_{file_type}_{result['sheet']}_{row_info['row_index']}_{i}"
                
                html_output += f"<p><input type='checkbox' id='{checkbox_id}'><label for='{checkbox_id}'>"
                html_output += f"<b>Row {row_info['row_index']}:</b></label></p>"
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

# === GRADIO INTERFACE ===

with gr.Blocks() as demo:
    gr.Markdown("# Calcolatore Prezzi Gi&Gi")
    gr.Markdown("Costi Macchina da QCC. Sono da aggiornare nel file config.txt.")
    # Display Tempo parameters at the very beginning
    with gr.Row():
        tempo1 = gr.Textbox(label="Costo Orario Forno Adesivo in Euro", value=config['tempo1'], interactive=False)
        tempo2 = gr.Textbox(label="Costo Orario Accoppiatrice in Euro", value=config['tempo2'], interactive=False)
        tempo3 = gr.Textbox(label="Costo Orario Termoadesivo in Euro", value=config['tempo3'], interactive=False)
    with gr.Row():
        tempon1 = gr.Textbox(label="Numero di Passaggi", value=1, interactive=True)
        tempon2 = gr.Textbox(label="Numero di Passaggi", value=0, interactive=True)
        tempon3 = gr.Textbox(label="Numero di Passaggi", value=0, interactive=True)


    gr.Markdown("Upload Excel files for Inventario to view their contents and search for specific values")
    
    # File upload components
    with gr.Row():
        inventario_file = gr.File(label="Upload Inventario Excel File", file_types=[".xlsx", ".xls"])
    
    # Search tuple input
    search_tuple_input = gr.Textbox(
        label="Search Tuple Values (comma-separated)",
        placeholder="Enter values to search for, comma separated"
    )
    
    # Search button
    search_button = gr.Button()
    
    # Event handling
    inventario_file.change(
        fn=lambda f: load_excel(f, "Inventario")[0] if f else "<h2>No Inventario file uploaded</h2>",
        inputs=inventario_file,
        #outputs=excel_output commented in order to avoid showing the file
    )
    
    # Search button click
    search_button.click(
        fn=search_in_excel,
        inputs=[inventario_file, search_tuple_input],
        #outputs=[search_output]
    )

# Launch the app
if __name__ == "__main__":
    demo.launch()

