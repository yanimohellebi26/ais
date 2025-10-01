from datetime import datetime

import pandas as pd

from sqlalchemy import text

from etl.utils.logger import Logger

from etl.Entity import Vessel, VesselType
from etl.utils.db import get_session


def get_vessels_db():
    with get_session() as session:
        result = session.execute(text(
            "SELECT * FROM vessel JOIN public.vessel_type vt on vessel.vessel_type_id = vt.id"
        )).mappings().all()
        df = pd.DataFrame.from_records(result)
        return df

def transform_vessel_delta(df):

    return df


def clear_vessels_db():
    with get_session() as session:
        session.execute(text("TRUNCATE TABLE vessel_type RESTART IDENTITY CASCADE"))
        session.execute(text("TRUNCATE TABLE vessel RESTART IDENTITY CASCADE"))
        session.commit()


def insert_test_data():
    with get_session() as session:
        # --- Create Vessel_type ---
        tanker = VesselType(id=1, description="Tanker")
        cargo = VesselType(id=2, description="Cargo")
        passenger = VesselType(id=3, description="Passenger")
        fishing = VesselType(id=4, description="Fishing")
        military = VesselType(id=5, description="Military")

        session.add_all([tanker, cargo, passenger, fishing, military])
        session.flush()

        # --- Create Vessel ---
        vessels = [
            Vessel(
                mmsi="123456789",
                imo="7654321",
                vessel_name="Poseidon",
                call_sign="PSDN",
                vessel_type_id=2,
                length=250.50,
                width=32.20,
                draft=10.5,
                transceiver_class="A",
                created_at=datetime.now(),
            ),
            Vessel(
                mmsi="987654321",
                imo="1234567",
                vessel_name="Neptune",
                call_sign="NPTN",
                vessel_type_id=2,
                length=180.75,
                width=25.00,
                draft=8.3,
                transceiver_class="A",
                created_at=datetime.now()
            ),
            Vessel(
                mmsi="111111111",
                imo="2222222",
                vessel_name="Hermes",
                call_sign="HRMS",
                vessel_type_id=3,
                length=120.0,
                width=20.0,
                draft=6.0,
                transceiver_class="B",
                created_at=datetime.utcnow(),
            ),
            Vessel(
                mmsi="222222222",
                imo="3333333",
                vessel_name="Athena",
                call_sign="ATHN",
                vessel_type_id=4,
                length=90.5,
                width=15.0,
                draft=4.5,
                transceiver_class="B",
                created_at=datetime.utcnow(),
            ),
            Vessel(
                mmsi="333333333",
                imo="4444444",
                vessel_name="Zeus",
                call_sign="ZEUS",
                vessel_type_id=5,
                length=300.0,
                width=40.0,
                draft=12.0,
                transceiver_class="A",
                created_at=datetime.utcnow(),
            ),
        ]

        for i in range(5, 10):
            vessels.append(
                Vessel(
                    mmsi=f"55555555{i}",
                    imo=f"777777{i}",
                    vessel_name=f"TestVessel{i}",
                    call_sign=f"TST{i}",
                    vessel_type_id=1 if i % 2 == 0 else 2,
                    length=100.0 + i * 10,
                    width=20.0 + i,
                    draft=5.0 + i * 0.5,
                    transceiver_class="B",
                    created_at=datetime.utcnow(),
                )
            )

        session.add_all(vessels)
        session.commit()
        Logger.success(f"Inserted {len(vessels)} vessels")
