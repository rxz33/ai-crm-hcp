from sqlalchemy.orm import Session
from app.db import models

def seed_hcps(db: Session):
    if db.query(models.HCP).count() > 0:
        return
    hcps = [
        models.HCP(name="Dr. Asha Sharma", specialty="Cardiology", city="Delhi"),
        models.HCP(name="Dr. Vikram Mehta", specialty="Diabetology", city="Mumbai"),
        models.HCP(name="Dr. Neha Verma", specialty="Dermatology", city="Bengaluru"),
    ]
    db.add_all(hcps)
    db.commit()

def list_hcps(db: Session):
    return db.query(models.HCP).order_by(models.HCP.name.asc()).all()

def create_interaction(db: Session, interaction: models.Interaction):
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return interaction

def get_interaction(db: Session, interaction_id: int):
    return db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()

def update_interaction_fields(db: Session, interaction: models.Interaction, updates: dict):
    for k, v in updates.items():
        if hasattr(interaction, k) and v is not None:
            setattr(interaction, k, v)
    db.commit()
    db.refresh(interaction)
    return interaction

def list_interactions_for_hcp(db: Session, hcp_id: int):
    return (
        db.query(models.Interaction)
        .filter(models.Interaction.hcp_id == hcp_id)
        .order_by(models.Interaction.id.desc())
        .all()
    )
