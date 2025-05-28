import pandas as pd
from io import BytesIO
import logging

_log = logging.getLogger(__name__)

# --- Helper Function for Excel Export ---
def to_excel(df: pd.DataFrame) -> bytes:
    """Converts a Pandas DataFrame to an Excel file in memory, ensuring index is the first column named 'Rečník'."""
    output = BytesIO()
    df_reset = df.reset_index()
    if not df_reset.empty:
        original_first_col_name = df_reset.columns[0]
        df_reset = df_reset.rename(columns={original_first_col_name: 'Rečník'})
        _log.info(f"Excel Export: Renamed first column '{original_first_col_name}' to 'Rečník'.")
    else:
        _log.warning("Excel Export: DataFrame is empty, cannot rename index column.")
        if df.index.name:
             df_reset[df.index.name] = []
             df_reset = df_reset.rename(columns={df.index.name: 'Rečník'})

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_reset.to_excel(writer, index=False, sheet_name='Matica_Rečník_Segment')
    processed_data = output.getvalue()
    return processed_data
