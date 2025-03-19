import pandas as pd
import numpy as np
import pycountry

# Set display options to show the entire DataFrame without truncation
pd.set_option('display.max_rows', None)  # Show all rows
pd.set_option('display.max_columns', None)  # Show all columns
pd.set_option('display.width', None)  # Avoid line wrapping
pd.set_option('display.max_colwidth', None)  # Show full content of columns


def get_dataframe_shape(df, context):
    """
    Get the shape (rows, columns) of a dataframe.
    """
    df_rows, df_cols = df.shape
    context["body"] += f"""
    1. Basic Table Information:
       - DataFrame has {df_rows} rows and {df_cols} columns.
    """
    

def check_column_spaces(df, context):
    """
    Identify columns with leading/trailing or inner spaces.
    """
    col_with_spaces = [col for col in df.columns if " " in col]
    if col_with_spaces:
        space_issue = f"Columns with spaces: {col_with_spaces}"
        context["action_items"] += f"    - Column name cleanup: Remove leading/trailing spaces in columns, or replace inner spaces with underscores (`_`) in the column {col_with_spaces}.\n"
        
    else:
        space_issue = "No column names have extra spaces."
    context["body"] += f"""
    2. Column Name Issues:
       - {space_issue}
    """


def check_duplicate_columns(df, context):
    """
    Identify duplicate column names.
    """
    duplicated_columns = df.columns[df.columns.duplicated()].tolist()
    if duplicated_columns:
        duplicate_issue = f"Duplicate column names found: {duplicated_columns}"
        context["action"] += f"    - Resolve duplicate columns: Consider to rename or remove duplicate column names {duplicated_columns} to maintain data integrity.\n"
    else:
        duplicate_issue = "No duplicate column names."
    context["body"] += f"   - {duplicate_issue}\n"
    

    
def _get_column_data_types(df, context):
    """
    Get a summary of column data types, missing values, and unique values.
    """
    dtype_info = pd.DataFrame({
        'Column': df.columns,
        'Data Type': df.dtypes.values,
        'Null Values': df.isnull().sum().values,
        'Unique Values': df.nunique().values
    }).sort_values(by="Null Values", ascending=False).reset_index(drop=True)

    return dtype_info

    
def get_column_data_types(df, context):
    dtype_info = _get_column_data_types(df, context)
    context["body"] += f"""
    3. Data Type Overview:
       {dtype_info.to_string(index=False)}
    """



def find_potential_primary_key(df, context):
    """
    Identify potential unique identifier columns in the given table (based on df).

    A unique identifier should:
    - Have no missing values (including NaN values).
    - Contain only unique values (no duplicates).
    """
    # Determine which table we're working with based on the column names
    if 'BARCODE' in df.columns and 'RECEIPT_ID' not in df.columns:
        identifier_columns = ['BARCODE']  # Product table
        table_name = 'product'
    elif 'RECEIPT_ID' in df.columns:
        identifier_columns = ['RECEIPT_ID']  # Transaction table (excluding BARCODE)
        table_name = 'transaction'
    elif 'ID' in df.columns:
        identifier_columns = ['ID']  # User table
        table_name = 'user'
    else:
        context["body"] += f"""
        4. Potential Unique Identifiers:
           - No unique identifier columns found in this table.
        """
        return

    invalid_identifiers = []

    # Check for unique identifiers in the provided table (ignoring NaN values)
    for col in identifier_columns:
        if col in df.columns:
            # Count missing values (NaN)
            nan_count = df[col].isna().sum()  # Count NaN values
            # Count duplicates (excluding NaN values)
            duplicate_count = df[col].dropna().duplicated().sum()

            # Add to invalid_identifiers if there are issues
            if nan_count > 0:
                invalid_identifiers.append(f"{col} in {table_name} table has {nan_count} missing values (NaN).")
            if duplicate_count > 0:
                invalid_identifiers.append(f"{col} in {table_name} table has {duplicate_count} duplicate values (excluding NaN).")

    # Identify other potential unique identifiers (excluding NaN values)
    unique_identifiers = [col for col in df.columns if df[col].dropna().duplicated().sum() == 0]

    if unique_identifiers:
        primary_key_check = f"Potential unique identifier(s): {unique_identifiers}."
    else:
        primary_key_check = "No unique and non-null identifier detected."

    if invalid_identifiers:
        primary_key_check += "\n       - Invalid unique identifiers: " + ", ".join(invalid_identifiers)
        context["action_items"] += f"    - Resolve issues with unique identifiers: {', '.join(invalid_identifiers)}\n"
    
    context["body"] += f"""
    4. Potential Unique Identifiers in {table_name} table:
       - {primary_key_check}
    """


 

def check_null_columns(df, context):
    """
    Identify columns that are fully null or partially null and calculate the percentage of missing values.
    """
    dtype_info = _get_column_data_types(df, context)
    check_col_null = dtype_info["Null Values"]
    rows = df.shape[0]

    if (check_col_null == rows).all():
        # Fully null columns
        full_null_cols = dtype_info.loc[check_col_null == rows, "Column"].tolist()
        null_columns_check = f"Fully NULL columns: {', '.join(full_null_cols)}."
        context["action_items"] += f"    - Handle fully NULL columns: Remove columns {', '.join(full_null_cols)} that contain only null values.\n"
    
    elif (check_col_null > 0).any():
        # Partially null columns with percentage calculation
        partial_null_df = dtype_info.loc[check_col_null > 0, ["Column", "Null Values"]].copy()
        partial_null_df["Null Percentage"] = (partial_null_df["Null Values"] / rows * 100).round(2)

        # Formatting the output message for partially null columns
        partial_null_details = [
            f"{row['Column']}: {row['Null Values']} missing ({row['Null Percentage']}%)"
            for _, row in partial_null_df.iterrows()
        ]
        partial_null_message = "\n          - " + "\n          - ".join(partial_null_details)

        context["action_items"] += f"    - Handle missing data: The following columns contain missing values:{partial_null_message}\n"
        null_columns_check = f"Partially NULL columns: {partial_null_message}"

    else:
        null_columns_check = "No NULL columns detected. All columns are fully populated."

    context["body"] += f"""
    5. Null Column Analysis:
       - {null_columns_check}
    """



def check_fully_duplicate_rows(df, context):
    """
    Identify fully duplicate rows.
    """
    fully_duplicate = df.duplicated().sum()
    if fully_duplicate == 0:
        duplicate_rows_check = "No fully duplicate rows."
    else:
        # Get examples of fully duplicate rows (up to 5 examples)
        duplicate_examples = df[df.duplicated(keep=False)].sort_values(by=df.columns.tolist()).head(5)

        # Format the output message
        duplicate_rows_check = f"There are {fully_duplicate} duplicate rows. Here are a few examples:\n{duplicate_examples.to_string(index=False)}"
        
        context["action_items"] += f"    - Remove duplicate rows: Consider to remove {fully_duplicate} duplicate entries. Example rows: \n{duplicate_examples.to_string(index=False)}\n"

    context["body"] += f"""
    6. Duplicate Row Analysis:
       - {duplicate_rows_check}
    """


def check_mixed_data_types(df, context):
    """
    Identify columns with mixed data types and list the different types present in those columns.
    """
    def check_column_type(x):
        # Handle cases where numeric values might be stored as strings
        if isinstance(x, (int, float)):
            return 'numeric'
        elif isinstance(x, str):
            try:
                # Try converting strings to numeric types (if possible)
                float(x)
                return 'numeric'
            except ValueError:
                return 'string'
        else:
            return type(x).__name__
    
    mixed_type_cols = []
    column_types = {}  # To store the different types found in each column
    
    for col in df.columns:
        types_in_col = df[col].dropna().apply(check_column_type).unique()
        if len(types_in_col) > 1:
            mixed_type_cols.append(col)
            column_types[col] = types_in_col
    
    if mixed_type_cols:
        mixed_data_types_check = f"Columns with mixed data types: {mixed_type_cols}."
        context["action_items"] += f"    - Resolve mixed data type issues: Standardize data types in the following columns: {mixed_type_cols} to ensure consistency.\n"
        
        # Adding the different types for the mixed columns
        type_details = "\n          - ".join([f"{col}: {', '.join(column_types[col])}" for col in mixed_type_cols])
        mixed_data_types_check += f"\n       - Different types in these columns:\n          - {type_details}"

    else:
        mixed_data_types_check = "No columns have mixed data types."
    
    context["body"] += f"""
    7. Mixed Data Type Check (e.g., numbers mixed with text): 
       - {mixed_data_types_check}
    """




def check_date_validity(df, context):
    """
    Ensure date timestamps in user and transaction tables are not in the future, with comparison in UTC.
    """
    invalid_dates = []
    date_columns = ['PURCHASE_DATE', 'SCAN_DATE', 'CREATED_DATE', 'BIRTH_DATE']
    found_date_columns = [col for col in date_columns if col in df.columns]
    
    if not found_date_columns:
        # No date columns found
        date_validity_check = "No date columns in this table."
    else:
        for col in found_date_columns:
            # Ensure the column is in UTC
            df[col] = pd.to_datetime(df[col], utc=True)
            
            # Get the current timestamp in UTC for comparison
            future_dates = df[df[col] > pd.Timestamp.now(tz='UTC')][col]
            if not future_dates.empty:
                invalid_dates.append(f"{col} has future dates: {', '.join(map(str, future_dates.unique()))}.")

        if invalid_dates:
            # If invalid dates are found
            date_validity_check = "\n       - ".join(invalid_dates)
            context["action_items"] += f"    - Correct invalid dates: Update or remove the following dates to ensure accuracy:\n       - {date_validity_check}\n"
        else:
            # If all date columns are valid
            date_validity_check = "All date columns are valid."

    # Add the result to the context
    context["body"] += f"""
    8. Date Validity Check (timestamps are valid): 
       - {date_validity_check}
    """


def check_transaction_date_order(df, context):
    """
    Check if 'scan_date' is aftwe 'transaction_date'. 
    If these columns do not exist, return 'No related columns'.
    """
    # Check if both 'SCAN_DATE' and 'PURCHASE_DATE' exist in the DataFrame
    if 'SCAN_DATE' in df.columns and 'PURCHASE_DATE' in df.columns:

        # Check if 'scan_date' is after 'purchase_date'
        invalid_dates = df[df['SCAN_DATE'].dt.date < df['PURCHASE_DATE'].dt.date]

        if not invalid_dates.empty:
            # Add the results to the context with details on invalid rows
            context["action_items"] += f"    - Correct date order: 'scan_date' should be after 'purchase_date'. Found invalid entries in {len(invalid_dates)} rows.\n"
            context["body"] += f"""
    9. Date Order Check (check if receipt scan date is after purchase date):
       - There are {len(invalid_dates)} rows where 'scan_date' is before 'purchase_date'.
    """
        else:
            context["body"] += """
    9. Date Order Check (check if receipt scan date is after purchase date):
       - All 'scan_date' entries are after 'purchase_date'.
    """
    else:
        context["body"] += """
    9. Date Order Check (check if receipt scan date is after purchase date):
       - No related columns found.
    """


def check_customer_date_order(df, context):
    """
    Check if 'scan_date' is aftwe 'transaction_date'. 
    If these columns do not exist, return 'No related columns'.
    """
    # Check if both 'SCAN_DATE' and 'PURCHASE_DATE' exist in the DataFrame
    if 'BIRTH_DATE' in df.columns and 'CREATED_DATE' in df.columns:

        # Check if 'created_date' is after 'birth_date'
        invalid_dates = df[df['CREATED_DATE'].dt.date < df['BIRTH_DATE'].dt.date]

        if not invalid_dates.empty:
            # Add the results to the context with details on invalid rows
            context["action_items"] += f"    - Correct date order: 'created_date' should be after 'birth_date'. Found invalid entries in {len(invalid_dates)} rows.\n"
            context["body"] += f"""
    10. Date Order Check (check if customers account created date is after birth date):
       - There are {len(invalid_dates)} rows where 'created_date' is before 'birth_date'.
    """
        else:
            context["body"] += """
    10. Date Order Check (check if customers account created date is after birth date):
       - All 'created_date' entries are after 'birth_date'.
    """
    else:
        context["body"] += """
    10. Date Order Check (check if customers account created date is after birth date):
       - No related columns found.
    """



def check_data_consistency(df, context):
    """
    Check if 'STATE' contains valid U.S. state abbreviations, 'LANGUAGE' contains valid language codes,
    and 'GENDER' contains consistent values. If these columns do not exist, return 'No related columns'.
    """
    # Define valid US state abbreviations
    valid_states = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'PR', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']
    
    # Define valid language codes (ISO 639-1)
    valid_languages = ['en', 'es-419', 'fr', 'de', 'it', 'pt', 'zh', 'ja', 'ko', 'ar', 'ru', 'hi', 'en-US', 'en-GB']
    
    # Define valid gender options
    valid_genders = [
        'female', 'male', 'non_binary', 'transgender', 'prefer_not_to_say', 'not_listed', 'unknown']

    # Check if 'STATE', 'LANGUAGE', and 'GENDER' exist in the DataFrame
    if 'STATE' in df.columns and 'LANGUAGE' in df.columns and 'GENDER' in df.columns:
        # Check invalid states
        invalid_states = df[~df['STATE'].isin(valid_states)]['STATE'].unique()
        
        # Check invalid languages
        invalid_languages = df[~df['LANGUAGE'].isin(valid_languages)]['LANGUAGE'].unique()
        
        # Check invalid genders
        invalid_genders = df[~df['GENDER'].isin(valid_genders)]['GENDER'].unique()
        
        # Ensure any NaN values are handled
        invalid_states = [str(state) if not pd.isna(state) else 'NaN' for state in invalid_states]
        invalid_languages = [str(language) if not pd.isna(language) else 'NaN' for language in invalid_languages]
        invalid_genders = [str(gender) if not pd.isna(gender) else 'NaN' for gender in invalid_genders]

        # Prepare body and action items
        context["body"] += """
    11. Data Consistency Check (check if STATE, LANGUAGE, and GENDER are consistent):
    """
        
        # If invalid states exist, list them in the body and action items
        if len(invalid_states) > 0:
            context["body"] += f"     - Invalid states detected: {', '.join(invalid_states)}\n"
            context["action_items"] += f"    - Resolve invalid states: Correct the following invalid states: {', '.join(invalid_states)}.\n"
        
        # If invalid languages exist, list them in the body and action items
        if len(invalid_languages) > 0:
            context["body"] += f"         - Invalid languages detected: {', '.join(invalid_languages)}\n"
            context["action_items"] += f"    - Resolve invalid languages: Correct the following invalid languages: {', '.join(invalid_languages)}.\n"
        
        # If invalid genders exist, list them in the body and action items
        if len(invalid_genders) > 0:
            context["body"] += f"         - Invalid gender values detected: {', '.join(invalid_genders)}\n"
            context["action_items"] += f"    - Resolve invalid gender values: Address the following invalid gender values: {', '.join(invalid_genders)}.\n"
        
    else:
        context["body"] += """
    11. Data Consistency Check (check if STATE, LANGUAGE, and GENDER are consistent):
       - No related columns found.
    """




def describe_data(df, context):
    """
    Generate summary statistics for the numeric columns in the DataFrame.
    If no numeric columns exist, return 'No numeric columns found'.
    """
    # Check if there are numeric columns in the DataFrame
    if df.select_dtypes(include=[np.number]).empty:
        context["body"] += """
    12. Summary Statistics:
       - No numeric columns found.
        """
        return

    # Generate summary statistics for numeric columns
    summary = df.describe(include=[np.number]).to_string(index=True)

    # Add the summary to the context
    context["body"] += f"""
    12. Summary Statistics:
       {summary}
    """




def print_summary(df):
    """
    Generate a detailed summary report of the dataframe.
    """
    TABLE_CHECK_STEPS = (
        get_dataframe_shape,
        check_column_spaces,
        check_duplicate_columns,
        get_column_data_types,
        find_potential_primary_key,
        check_null_columns,
        check_fully_duplicate_rows,
        check_mixed_data_types,
        check_date_validity,
        check_transaction_date_order,
        check_customer_date_order, 
        check_data_consistency, 
        describe_data, 
    )

    context = {
        "body": f"Here is the result of the initial data check for of table '{df.name}':\n",
        "action_items": "Action required:\n",
    }

    for step in TABLE_CHECK_STEPS:
        step(df, context)

    return f"""
    {context["body"]}
    \n
    {context["action_items"]}
    """