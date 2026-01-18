from typing import Any, Dict, Optional
import json, re
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db import models

def merge_json_safely(raw: str) -> Dict[str, Any]:
    if not raw:
        return {}
    raw = raw.strip()

    # strip code fences
    raw = re.sub(r"^```(json)?", "", raw, flags=re.IGNORECASE).strip()
    raw = re.sub(r"```$", "", raw).strip()

    # strict parse
    try:
        return json.loads(raw)
    except Exception:
        pass

    # extract first {...}
    m = re.search(r"\{[\s\S]*\}", raw)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except Exception:
        return {}

def resolve_hcp_by_name_or_id(db: Session, hcp_id: Optional[int], hcp_name: Optional[str]) -> Optional[models.HCP]:
    if hcp_id:
        return db.query(models.HCP).filter(models.HCP.id == int(hcp_id)).first()
    if hcp_name:
        return db.query(models.HCP).filter(func.lower(models.HCP.name) == hcp_name.strip().lower()).first()
    return None
