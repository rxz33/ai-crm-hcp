from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app import crud
from app.schemas import HCPOut

router = APIRouter(prefix="/hcps", tags=["hcps"])

@router.get("", response_model=list[HCPOut])
def get_hcps(db: Session = Depends(get_db)):
    crud.seed_hcps(db)
    return crud.list_hcps(db)
