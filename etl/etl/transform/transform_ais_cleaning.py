import pandas as pd

from etl.utils.logger import Logger

input_csv = r"C:\Users\lenam\Documents\M1\Projet\ais\etl\data\local\downloads\AIS_test_data.csv"
output_csv = "vessels_cleaned.csv"
id_col = "mmsi"
date_col = "date"

column_names = [
    "mmsi", "date", "lat", "lon", "sog", "cog", "heading", "vessel_name", "imo", "callsign", "vessel_type", "status",
    "length", "width", "draft", "cargo", "transceiver_class"
]

df = pd.read_csv(input_csv, header=None, names=column_names)

df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

df = df.sort_values(by=date_col, ascending=False)


# function that merges duplicates
def merge_rows(group):
    merged = {}
    for col in group.columns:
        non_na = group[col].dropna()
        merged[col] = non_na.iloc[0] if not non_na.empty else pd.NA
    return pd.Series(merged)


# merging of lines with the same mmsi
group_sizes = df.groupby(id_col).size()
df_cleaned = df.groupby(id_col, as_index=False).apply(merge_rows)

# logging of deleted duplicates
duplicates_info = group_sizes[group_sizes > 1]
Logger.info(f"Total duplicates removed : {duplicates_info.sum() - len(duplicates_info)}")

df_cleaned.to_csv(output_csv, index=False)
Logger.info(f"Cleaning complete. Total lines retained : {len(df_cleaned)}")

print(f"Cleaning complete. File saved as {output_csv}")
print(df_cleaned.head())
