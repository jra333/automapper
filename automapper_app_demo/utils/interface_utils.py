import streamlit as st
import pandas as pd
import uuid
from datetime import datetime
import re
from io import StringIO
import logging
from utils.file_processor import process_file
import os
#from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, StAggridTheme

logger = logging.getLogger(__name__)

def highlight_differences(row):

    """Highlight differences between actual and predicted values"""
    styles = [''] * len(row)
    columns = row.index.astype(str)
    for i, col in enumerate(columns):
        if col.startswith('Predicted '):
            actual_col = 'Actual ' + col.split('Predicted ')[1]
            if actual_col in columns and row[actual_col] != row[col]:
                styles[i] = 'background-color: yellow'
    return styles

def validate_placement_groups(df):
    """
    Reads the master mediaplan file and returns a styled DataFrame in which 
    the cells for Placement Group, Tactic, Audience, and Ad Type are validated.
    
    """
    valid_path = os.path.join("data_db", "your_data.csv")
    if os.path.exists(valid_path):
        valid_df = pd.read_csv(valid_path)
        group_map = {}
        for _, row in valid_df.iterrows():
            pg = str(row.get("PLACEMENT_GROUP", "")).strip()
            if pg and pg not in group_map:
                group_map[pg] = {
                    "Tactic": str(row.get("TACTIC", "")).strip(),
                    "Audience": str(row.get("AUDIENCE", "")).strip(),
                    "Ad Type": str(row.get("AD_TYPE", "")).strip()
                }
    
        def highlight_validations(row):
            styles = [''] * len(row)
            cols = row.index.tolist()
    
            # Get the row values from the processed DataFrame
            pg_val = str(row.get("Placement Group", "")).strip()
            tactic_val = str(row.get("Tactic", "")).strip()
            audience_val = str(row.get("Audience", "")).strip()
            ad_type_val = str(row.get("Ad Type", "")).strip()
    
            # Define style colors
            green = "background-color: green"
            red = "background-color: red"
    
            if pg_val in group_map:
                ref = group_map[pg_val]
                # Highlight individual cells
                for i, col in enumerate(cols):
                    if col == "Placement Group":
                        styles[i] = green
                    elif col == "Tactic":
                        styles[i] = green if tactic_val == ref.get("Tactic", "") else red
                    elif col == "Audience":
                        styles[i] = green if audience_val == ref.get("Audience", "") else red
                    elif col == "Ad Type":
                        styles[i] = green if ad_type_val == ref.get("Ad Type", "") else red
            else:
                # If the placement group is not found in the master, mark validation cells as red.
                for i, col in enumerate(cols):
                    if col in ["Placement Group", "Tactic", "Audience", "Ad Type"]:
                        styles[i] = red
            return styles
    
        return df.style.apply(highlight_validations, axis=1)
    else:
        logger.warning("your_data.csv not found for placement group validation.")
        return df

def display_edit_interface(df):
    """Display the edit interface"""
    # Initialize all session state variables
    if 'edited_df' not in st.session_state:
        # Convert Media ID to string to avoid Arrow serialization issues
        df = df.copy()
        if 'Media ID' in df.columns:
            df['Media ID'] = df['Media ID'].astype(str)
        st.session_state.edited_df = df
    if 'original_df' not in st.session_state:
        st.session_state.original_df = df.copy()
    if 'expanded_rows' not in st.session_state:
        st.session_state.expanded_rows = set()
    if 'changes_saved' not in st.session_state:
        st.session_state.changes_saved = False
    if 'final_df' not in st.session_state:
        st.session_state.final_df = None
    
    #st.subheader("Interactive Data Editor")

    # Editor and Changes tabs
    tab1, tab2 = st.tabs(["🖊 Data Editor", "📊 Changes and Download"])
    

    with tab1:
        st.subheader("Interactive Data Editor")
        st.markdown("Double click on a cell to edit it. Press 'Apply Changes' to save your changes.")
        # Search and filter
        col1, col2 = st.columns([3, 1])
        with col1:
            search_term = st.text_input("🔍 Search Placements", help="Filter rows by placement name or campaign")
        with col2:
            sort_by = st.selectbox("Sort by", ["Campaign", "Placement Name", "Publisher"])
        
        # Filter and sort data
        filtered_df = st.session_state.edited_df.copy()
        if search_term:
            mask = (
                filtered_df['Placement Name'].str.contains(search_term, case=False, na=False) |
                filtered_df['Campaign'].str.contains(search_term, case=False, na=False)
            )
            filtered_df = filtered_df[mask]
        filtered_df = filtered_df.sort_values(sort_by).reset_index(drop=True)
        
        # Define which columns are editable
        editable_columns = ['Placement Name', 'Publisher', 'Placement Group', 'Tactic', 'Audience', 'Ad Type']
        column_config = {col: st.column_config.TextColumn(col, width="medium") for col in editable_columns}
        
        # Display editable dataframe
        edited_df = st.data_editor(
            filtered_df,
            column_config=column_config,
            num_rows="dynamic",
            use_container_width=True,
            height=500,
            disabled=["Campaign"]  # Make Campaign column read-only
        )
        
        if st.button("Apply Changes"):
            st.session_state.edited_df = edited_df
            st.session_state.final_df = edited_df
            st.session_state.changes_saved = True
            st.success("Changes applied!")
    
    with tab2:
        if st.session_state.edited_df is not None:
            st.success("✅ Review your changes below.")
            
            # Display the updated dataframe
            st.markdown("##### Updated Data Preview")
            st.dataframe(st.session_state.edited_df, use_container_width=True)
            
            # Download button for changes
            st.download_button(
                label="📥 Download Updated Data",
                data=st.session_state.edited_df.to_csv(index=False),
                file_name="updated_data.csv",
                mime="text/csv",
                key='download-csv'
            )
        else:
            st.info("💡 Make changes in the Data Editor tab to see them here.")

    # When displaying the data, validate and highlight Placement Group entries:
    st.markdown("### Validate Placement Groups")
    st.markdown("This will highlight in green any placement groups that are found in the master mediaplan file.")
    validated_df = validate_placement_groups(st.session_state.edited_df)
    st.dataframe(validated_df)

def display_mapper_interface():
    """Display interface for Mapper accounts"""
    st.title("Automapper v2.0 (Local DB Connection)")
    st.subheader("TEAM NAME")
    st.markdown("***Model last trained: 01/30/2025***")
    st.markdown("---")
    st.markdown("### Instructions")
    st.markdown("1. Upload required file OR a raw file (min required columns: campaign, placement name).")
    st.markdown("2. Click 'Confirm and Continue' to process your data.")
    st.markdown("3. Review the processed data and make any necessary edits.")
    st.markdown("4. Click 'Save All Changes' to save your changes.")
    st.markdown("5. Download the updated data to your local machine.")
    st.markdown("Placement group validation is provided at the bottom of the data editor tab by cross referencing the master mediaplan file.")
    

    # Initialize all session state variables
    if 'processed_df' not in st.session_state:
        st.session_state.processed_df = None
    if 'current_file_name' not in st.session_state:
        st.session_state.current_file_name = None
    if 'changes_saved' not in st.session_state:
        st.session_state.changes_saved = False
    
    uploaded_file = st.file_uploader(
        "Choose a file", 
        type=['csv', 'xlsx'],
        help="Upload a CSV or Excel file"
    )
    
    if uploaded_file:
        try:
            file_changed = (
                st.session_state.current_file_name != uploaded_file.name
            )
            
            if file_changed:
                # Read and process the file
                if uploaded_file.name.endswith('.csv'):
                    uploaded_file.seek(0)
                    original_df = pd.read_csv(uploaded_file)
                elif uploaded_file.name.endswith('.xlsx'):
                    uploaded_file.seek(0)
                    try:
                        original_df = pd.read_excel(uploaded_file, engine='openpyxl')
                    except Exception as e:
                        st.error("There was an error reading the Excel file. Please ensure it is a valid .xlsx file.")
                        logger.error("Error reading Excel file", exc_info=True)
                        return
                else:
                    st.error("Unsupported file type. Please upload a CSV or XLSX file.")
                    return
                
                original_df2 = original_df.copy()

                with st.spinner("Cleaning data..."):
                    # Convert Media ID to string if it exists
                    if 'Media ID' in original_df.columns:
                        original_df['Media ID'] = original_df['Media ID'].astype(str)

                
                    # Clean PLACEMENT_NAME column: remove text occurring after ":D"
                    if 'Placement Name' in original_df.columns:
                        original_df['Placement Name'] = original_df['Placement Name'].apply(
                            lambda x: x.split(":D")[0].strip() if isinstance(x, str) and ":D" in x else x
                        )

                # --- VLOOKUP STEP FOR MISSING PLACEMENT_NAME ---
                if 'Placement Name' in original_df.columns:
                    missing_mask = original_df["Placement Name"].isna() | (original_df["Placement Name"].astype(str).str.strip() == "")
                    if missing_mask.any():
                        with st.spinner("Looking up missing placement names..."):
                            dcm_path = os.path.join("data_db", "your_data.csv")
                            if os.path.exists(dcm_path):
                                dcm_df = pd.read_csv(dcm_path)
                                # Ensure the lookup key in dcm_df is a string to match "Media ID"
                                dcm_df["PLACEMENT_ID_AD_SET_ID"] = dcm_df["PLACEMENT_ID_AD_SET_ID"].astype(str)
                                mapping = dcm_df.set_index("PLACEMENT_ID_AD_SET_ID")["PLACEMENT_NAME_AD_SET_NAME"].to_dict()
                                # Map using "Media ID" from original_df cast as string
                                original_df.loc[missing_mask, "Placement Name"] = (
                                    original_df.loc[missing_mask, "Media ID"].astype(str).map(mapping)
                                )
                                logger.info("Filled missing Placement Name values using lookup from your_data.csv.")
                            else:
                                logger.warning("your_data.csv not found; missing placement names remain unfilled.")
                # --- END VLOOKUP STEP ---

                
                # Process the file
                with st.spinner("Processing file with AI predictions..."):
                    processed_df = process_file(original_df)
                
                st.session_state.processed_df = processed_df
                st.session_state.current_file_name = uploaded_file.name
                st.session_state.changes_saved = False  # Reset changes_saved flag
                
                # Show preview
                tab1, tab2 = st.tabs(["Original Data", "Processed Data"])
                with tab1:
                    st.dataframe(original_df2, use_container_width=True)
                with tab2:
                    st.dataframe(processed_df, use_container_width=True)
                
                if st.button("Confirm and Continue", type="primary"):
                    display_edit_interface(st.session_state.processed_df)
            else:
                display_edit_interface(st.session_state.processed_df)
            
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            logger.error(f"File processing error: {str(e)}", exc_info=True)