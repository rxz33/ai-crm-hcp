from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Text, ForeignKey, Integer, Boolean, func

class Base(DeclarativeBase):
    pass

class HCP(Base):
    __tablename__ = "hcps"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    specialty: Mapped[str] = mapped_column(String(120), default="")
    city: Mapped[str] = mapped_column(String(120), default="")

    interactions = relationship("Interaction", back_populates="hcp")

class Interaction(Base):
    __tablename__ = "interactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    hcp_id: Mapped[int] = mapped_column(ForeignKey("hcps.id"), index=True)

    interaction_type: Mapped[str] = mapped_column(String(50), default="Visit")

    # New structured fields (match video UI)
    date: Mapped[str] = mapped_column(String(12), default="")   # YYYY-MM-DD
    time: Mapped[str] = mapped_column(String(8), default="")    # HH:MM
    attendees: Mapped[str] = mapped_column(Text, default="")
    topics_discussed: Mapped[str] = mapped_column(Text, default="")
    materials_shared: Mapped[str] = mapped_column(Text, default="")     # comma-separated for MVP
    samples_distributed: Mapped[str] = mapped_column(Text, default="")  # comma-separated for MVP
    consent_required: Mapped[bool] = mapped_column(Boolean, default=False)

    # Existing fields
    occurred_at: Mapped[str] = mapped_column(String(40), default="")
    sentiment: Mapped[str] = mapped_column(String(20), default="neutral")
    products_discussed: Mapped[str] = mapped_column(String(255), default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    outcomes: Mapped[str] = mapped_column(Text, default="")
    follow_ups: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    hcp = relationship("HCP", back_populates="interactions")
