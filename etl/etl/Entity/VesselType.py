from __future__ import annotations
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship, Mapped, mapped_column
from .base import Base

class VesselType(Base):
    __tablename__ = "vessel_type"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    description: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    vessel_group: Mapped[str] = mapped_column(String(20))
