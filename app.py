"""
Lead Categorization Application

This Streamlit app categorizes leads based on their website activity journey.
"""

import streamlit as st
import pandas as pd
import re
from urllib.parse import urlparse

all_lead_categories_options = [
    "Neighborhood: Downtown Fort Lauderdale",
    "Neighborhood: Las Olas Isles",
    "Neighborhood: Bermuda Riviera",
    "Neighborhood: Lauderdale Harbours",
    "Neighborhood: Fort Lauderdale Beach",
    "Neighborhood: Coral Ridge",
    "Neighborhood: Rio Vista",
    "Neighborhood: Victoria Park",
    "Neighborhood: Tarpon River",
    "Neighborhood: Lake Ridge",
    "Condo: NuRiver Landing Condo",
    "Condo: Watergarden",
    "Condo: Symphony",
    "Condo: Las Olas Grand",
    "Condo: 100 Las Olas",
    "Condo: Las Olas By The River",
    "Condo: Las Olas River House",
    "Condo: Strada",
    "Condo: Waverly",
    "Condo: NuRiver Landing",
    "New Construction",
    "Waterfront Homes",
    "High Rise Riverfront Condos",
    "other",
    "BUY",
    "SELL",
    "GENERAL"
]


def normalize_url(url):
    """
    Normalizes a URL by converting to lowercase, stripping whitespace, and returning the path.

    Args:
        url (str): The URL to normalize

    Returns:
        str: The normalized URL path
    """
    url = url.lower().strip()
    parsed = urlparse(url)
    return parsed.path


def categorize_leads(leads_df, priority_list, category_map, column_name):
    """
    Main logic function to categorize leads based on their website journey URLs.

    Args:
        leads_df (pd.DataFrame): DataFrame containing lead data
        priority_list (list): List of categories in priority order
        category_map (dict): Mapping of URL patterns to categories
        column_name (str): Name of the column containing journey data

    Returns:
        list: List of categories assigned to each lead
    """

    def parse_journey(row):
        """
        Parse journey data to extract URLs from various formats.

        Args:
            row: Journey data (string representation of URL list)

        Returns:
            list: List of extracted URLs
        """
        # Handle both full URLs and path-only formats
        # First try to find full URLs
        url_list = re.findall(r'https?://[^\s,\]]+', str(row))

        # If no full URLs found, look for paths (starting with /)
        if not url_list:
            url_list = re.findall(r'/[a-zA-Z0-9\-\/_]+', str(row))

        if not url_list:
            url_list = []
        return url_list

    matched_categories = set()
    categories = []

    for row in leads_df[column_name].tolist():
        row = parse_journey(row)
        matched_categories.clear()

        for item in row:
            item = normalize_url(item)
            for key in category_map:
                if key.lower() in item.lower():
                    matched_categories.add(category_map[key])

        final_category = 'GENERAL'

        for priority in priority_list:
            if priority in matched_categories:
                final_category = priority
                break

        categories.append(final_category)
    return categories


def load_data(file):
    """
    Load data from CSV files with error handling.

    Args:
        file: File object from Streamlit file uploader

    Returns:
        pd.DataFrame or None: Loaded DataFrame or None if error occurred
    """
    try:
        df = pd.read_csv(file)
        return df
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None


def save_changes_callback():
    """
    Callback function to save changes when filter changes.
    """
    if 'pending_changes' in st.session_state and st.session_state.pending_changes is not None:
        # Apply pending changes to the main dataset
        if 'current_filter_value' in st.session_state:
            filter_val = st.session_state.current_filter_value
            if filter_val != 'All':
                # Update only filtered rows
                for idx, row in st.session_state.pending_changes.iterrows():
                    st.session_state.master_data.loc[idx] = row
            else:
                # Update entire dataset
                st.session_state.master_data = st.session_state.pending_changes.copy()
        
        # Clear pending changes
        st.session_state.pending_changes = None


def main():
    """
    Main function that runs the Streamlit lead categorization application.
    """
    st.title("Jason's Lead Categorizer")

    st.write("This app categorizes leads based on their website activity. Upload your lead data CSV file to get started.")
    st.write("**Note:** The lead data must contain a 'journey' column with URLs representing the user's website journey.")

    # Initialize session state for data persistence
    if 'master_data' not in st.session_state:
        st.session_state.master_data = None
    if 'file_hash' not in st.session_state:
        st.session_state.file_hash = None
    if 'pending_changes' not in st.session_state:
        st.session_state.pending_changes = None
    if 'current_filter_value' not in st.session_state:
        st.session_state.current_filter_value = 'All'

    # file upload widget
    leads_file = st.file_uploader("Upload Lead Data CSV", type=["csv"])

    if leads_file:
        # Create a hash of the uploaded file to detect if it's a new file
        file_hash = hash(leads_file.getvalue())

        # Check if this is a new file upload
        is_new_file = st.session_state.file_hash != file_hash

        if is_new_file:
            # New file uploaded, process it
            leads_df = load_data(leads_file)
            st.session_state.file_hash = file_hash

            # Load mapping.csv from the current directory
            try:
                category_df = pd.read_csv('mapping.csv')
            except FileNotFoundError:
                st.error("mapping.csv file not found in the application directory. Please ensure the mapping file exists.")
                return
            except Exception as e:
                st.error(f"Error loading mapping.csv: {e}")
                return

            # check if dfs are compatible
            if leads_df is None:
                return

            if 'URL' not in category_df.columns or 'TYPE' not in category_df.columns:
                st.error("The mapping.csv file is corrupted. Please contact support.")
                return
            if 'journey' not in leads_df.columns:
                st.error("The lead data must contain a 'journey' column. Please make sure your CSV file has the correct format with a 'journey' column containing website URLs.")
                return

            column_name = 'journey'

            category_map = dict(zip(category_df['URL'], category_df['TYPE']))
            category_map = {k.lower(): v for k, v in category_map.items()}

            leads_df['TYPE'] = categorize_leads(leads_df, all_lead_categories_options, category_map, column_name)

            # Reorder columns
            cols = ['TYPE'] + [col for col in leads_df.columns if col != 'TYPE']
            leads_df = leads_df[cols]

            # Store the newly categorized data in session state
            st.session_state.master_data = leads_df.copy()

        # Use master data if available
        if st.session_state.master_data is not None:
            display_data = st.session_state.master_data.copy()
        else:
            st.error("No data available. Please upload a file.")
            return

        # Add filter widget
        st.subheader("Filter Data")

        # Get unique categories for filter options
        unique_categories = sorted(display_data['TYPE'].unique())
        filter_options = ['All'] + unique_categories

        # Check if filter changed and save pending changes
        selected_filter = st.selectbox(
            "Filter by TYPE:",
            options=filter_options,
            index=0,
            help="Select a category to filter the data, or 'All' to show all records",
            on_change=save_changes_callback
        )

        # Update current filter value
        st.session_state.current_filter_value = selected_filter

        # Apply filter
        if selected_filter != 'All':
            filtered_data = display_data[display_data['TYPE'] == selected_filter].copy()
        else:
            filtered_data = display_data.copy()

        st.write(f"Showing {len(filtered_data)} of {len(display_data)} records")

        # Data editor without automatic session state updates
        edited_leads_df = st.data_editor(
            filtered_data,
            column_config={
                'TYPE': st.column_config.SelectboxColumn(
                        "TYPE",
                        options=all_lead_categories_options,
                        required=True,
                        help="Assign a category or neighborhood to this lead (e.g., Buy, Sell, Other)"
                    ),
            },
            hide_index=True,
            use_container_width=True
        )

        # Store pending changes (don't update master data immediately)
        if not edited_leads_df.equals(filtered_data):
            st.session_state.pending_changes = edited_leads_df.copy()
            st.info("Changes will be saved automatically when you switch filters or can be saved manually below.")
            
            # Manual save button for immediate saving
            if st.button("Save Changes Now"):
                save_changes_callback()
                st.success("Changes saved!")
                st.rerun()

        # save categorized leads to a downloadable CSV file
        output_file = "categorized_leads.csv"
        final_data = st.session_state.master_data
        final_data.to_csv(output_file, index=False)
        st.success(f"Categorized leads saved to {output_file}. You can download it below.")
        with open(output_file, "rb") as f:
            st.download_button(
                label="Download Categorized Leads (All Data)",
                data=f,
                file_name=output_file,
                mime='text/csv'
            )


if __name__ == "__main__":
    main()
