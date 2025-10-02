from __future__ import annotations
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, Numeric, TIMESTAMP, ForeignKey, Boolean, func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from .base import Base

class Vessel(Base):
    __tablename__ = "vessel"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mmsi: Mapped[str] = mapped_column(String(9), nullable=False, unique=True)
    imo: Mapped[Optional[str]] = mapped_column(String(7))
    vessel_name: Mapped[Optional[str]] = mapped_column(String(50))
    call_sign: Mapped[Optional[str]] = mapped_column(String(20))

    vessel_type_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("vessel_type.id"))
    cargo_type_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("vessel_type.id"))

    length: Mapped[Optional[float]] = mapped_column(Numeric(6, 2))
    width: Mapped[Optional[float]] = mapped_column(Numeric(6, 2))
    draft: Mapped[Optional[float]] = mapped_column(Numeric(4, 2))
    transceiver_class: Mapped[Optional[str]] = mapped_column(String(20))
    created_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)
    locked : Mapped[Optional[bool]] = mapped_column(Boolean)
    last_update = mapped_column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    vessel_type: Mapped[Optional["VesselType"]] = relationship(
        "VesselType",
        back_populates="vessels_as_type",
        foreign_keys=[vessel_type_id]
    )
    cargo_type: Mapped[Optional["VesselType"]] = relationship(
        "VesselType",
        back_populates="vessels_as_cargo",
        foreign_keys=[cargo_type_id]
    )

    def __repr__(self):
        return f"<Vessel(id={self.id}, name={self.vessel_name}, mmsi={self.mmsi})>"
