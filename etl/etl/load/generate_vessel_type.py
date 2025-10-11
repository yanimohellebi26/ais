import os

import pandas as pd

from etl.utils.logger import Logger


def load_vessel_type(data: pd.DataFrame, output_path : str = "insert_vessels_type.sql"):
    """
    Generate SQL migration for vessels types
    Args:
        data: vessels code data
        output_path: sql migration file path to generate

    Returns:
    """
    download_folder = os.getenv("GENERATED_FOLDER")
    path = os.path.join(download_folder, output_path)

    values = []
    for _, row in data.iterrows():
        ids = str(row['id']).split('-')
        start = int(ids[0])
        end = int(ids[-1]) + 1

        for i in range(start, end):
            desc = str(row["description"]).replace("'", "''")
            group = str(row["vessel_group"]).replace("'", "''")
            values.append(f"({i}, '{desc}', '{group}')")

        sql = (
                "-- Migration : INSERT Vessel types\n"
                "BEGIN;\n"
                "INSERT INTO vessel_type (id, description, vessel_group) VALUES\n"
                + ",\n".join(values)
                + ";\nCOMMIT;"
        )

        with open(path, "w", encoding="utf-8") as f:
            f.write(sql)

    Logger.success(f"Migration {path} has been generated.")

