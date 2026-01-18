from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db import models
from app.agent.utils import resolve_hcp_by_name_or_id

# ----------------------------------
# Tool 1: Log Interaction (required)
# ----------------------------------

def tool_log_interaction(db: Session, draft: Dict[str, Any]) -> Dict[str, Any]:
    # resolve HCP by id or name (video-style, no dropdown required)
    hcp_id = draft.get("hcp_id") or None
    hcp_name = draft.get("hcp_name") or None

    hcp = resolve_hcp_by_name_or_id(db, hcp_id, hcp_name)

    # If HCP not found but name exists, create it (optional; good for demo)
    if not hcp and hcp_name:
        hcp = models.HCP(name=hcp_name.strip(), specialty="", city="")
        db.add(hcp)
        db.commit()
        db.refresh(hcp)

    if not hcp:
        return {"error": "HCP is required to log. Please mention HCP name in chat."}

    interaction = models.Interaction(
        hcp_id=hcp.id,
        interaction_type=draft.get("interaction_type", "Meeting"),

        date=draft.get("date",""),
        time=draft.get("time",""),
        attendees=draft.get("attendees",""),
        topics_discussed=draft.get("topics_discussed",""),
        materials_shared=draft.get("materials_shared",""),
        samples_distributed=draft.get("samples_distributed",""),
        consent_required=bool(draft.get("consent_required", False)),

        occurred_at=draft.get("occurred_at",""),
        sentiment=draft.get("sentiment","neutral"),
        products_discussed=draft.get("products_discussed",""),
        summary=draft.get("summary",""),
        outcomes=draft.get("outcomes",""),
        follow_ups=draft.get("follow_ups",""),
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)

    return {"interaction_id": interaction.id, "hcp_id": hcp.id, "message": "Logged interaction successfully."}

# ----------------------------
# Tool 2: Edit Interaction (required, no interaction_id in UI)
# ----------------------------

def tool_edit_latest_interaction(db: Session, hcp_id: Optional[int], hcp_name: Optional[str], fields_to_update: Dict[str, Any]) -> Dict[str, Any]:
    hcp = resolve_hcp_by_name_or_id(db, hcp_id, hcp_name)
    if not hcp:
        return {"error": "HCP not found for edit. Please mention the HCP name."}

    target = (
        db.query(models.Interaction)
        .filter(models.Interaction.hcp_id == hcp.id)
        .order_by(desc(models.Interaction.created_at))
        .first()
    )
    if not target:
        return {"error": "No interactions found for this HCP to edit."}

    # patch only allowed fields
    allowed = {
        "interaction_type","date","time","attendees","topics_discussed",
        "materials_shared","samples_distributed","consent_required",
        "occurred_at","sentiment","products_discussed","summary","outcomes","follow_ups"
    }

    updated = {}
    for k, v in (fields_to_update or {}).items():
        if k in allowed and v is not None:
            setattr(target, k, v)
            updated[k] = v

    db.commit()

    return {
        "tool_used": "EditInteraction",
        "interaction_id": target.id,
        "hcp_id": hcp.id,
        "updated_fields": updated,
        "message": f"Updated latest interaction for {hcp.name}."
    }

# ----------------------------
# Tool 3: Retrieve HCP Context
# ----------------------------
def tool_retrieve_hcp_context(db: Session, hcp_id: Optional[int] = None, hcp_name: Optional[str] = None) -> Dict[str, Any]:
    hcp = resolve_hcp_by_name_or_id(db, hcp_id, hcp_name)
    if not hcp:
        return {"error": "HCP not found"}

    latest = (
        db.query(models.Interaction)
        .filter(models.Interaction.hcp_id == hcp.id)
        .order_by(desc(models.Interaction.created_at))
        .limit(5)
        .all()
    )

    return {
    "hcp": {"id": hcp.id, "name": hcp.name, "specialty": hcp.specialty, "city": hcp.city},
    "latest_interactions": [
        {
            "id": i.id,
            "created_at": str(i.created_at),

            "interaction_type": i.interaction_type,
            "date": i.date,
            "time": i.time,
            "attendees": i.attendees,
            "topics_discussed": i.topics_discussed,
            "materials_shared": i.materials_shared,
            "samples_distributed": i.samples_distributed,
            "consent_required": i.consent_required,

            "occurred_at": i.occurred_at,
            "sentiment": i.sentiment,
            "products_discussed": i.products_discussed,
            "summary": i.summary,
            "outcomes": i.outcomes,
            "follow_ups": i.follow_ups,
        }
        for i in latest
    ],
}


# ----------------------------
# Tool 4: Follow-up Suggestions
# ----------------------------
def tool_followup_suggestions(draft: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[str]:
    # MVP: deterministic suggestions + a few heuristics
    suggestions = []

    if draft.get("materials_shared"):
        suggestions.append("Confirm materials were received and answer any follow-up questions")
    else:
        if draft.get("products_discussed"):
            suggestions.append("Share brochure/clinical highlights for discussed products")

    if draft.get("sentiment") in ["neutral", "negative"]:
        suggestions.append("Address objections and share evidence/clinical study summary")
    suggestions.append("Schedule next follow-up in 2 weeks")

    # ensure unique, keep max 6
    uniq = []
    for s in suggestions:
        if s not in uniq:
            uniq.append(s)
    return uniq[:6]

# ----------------------------
# Tool 5: Compliance Check
# ----------------------------
def tool_compliance_check(draft: Dict[str, Any]) -> Dict[str, Any]:
    issues = []

    # consent gating example
    if draft.get("used_voice_note") and not draft.get("consent_required"):
        issues.append("Consent not confirmed for voice note summarization")

    risky_words = ["guarantee", "100% effective", "cure"]
    text_blob = " ".join([
        str(draft.get("summary","")),
        str(draft.get("outcomes","")),
        str(draft.get("topics_discussed",""))
    ]).lower()

    for w in risky_words:
        if w in text_blob:
            issues.append(f"Risky claim detected: '{w}'")

    status = "ok" if not issues else "review"
    return {"status": status, "issues": issues}

