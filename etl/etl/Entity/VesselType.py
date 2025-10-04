from __future__ import annotations
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship, Mapped, mapped_column
from .base import Base

class VesselType(Base):
    __tablename__ = "vessel_type"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    description: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    vessels_as_type: Mapped[list["Vessel"]] = relationship(
        "Vessel", back_populates="vessel_type", foreign_keys="[Vessel.vessel_type_id]"
    )
    vessels_as_cargo: Mapped[list["Vessel"]] = relationship(
        "Vessel", back_populates="cargo_type", foreign_keys="[Vessel.cargo_type_id]"
    )
