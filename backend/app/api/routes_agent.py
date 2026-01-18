from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.agent.graph import agent_app
from app.agent.tools import (
    tool_log_interaction,
    tool_edit_latest_interaction,
    tool_retrieve_hcp_context,
    tool_followup_suggestions,
    tool_compliance_check,
)

router = APIRouter(prefix="/agent", tags=["agent"])


# ----------------------------
# Chat (LangGraph orchestrator)
# ----------------------------
@router.post("/chat")
def agent_chat(payload: Dict[str, Any], db: Session = Depends(get_db)) -> Dict[str, Any]:
    message = (payload.get("message") or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="message is required")

    draft = payload.get("draft") or {}

    state_in = {
        "message": message,
        "mode": payload.get("mode") or "draft",
        "draft": draft,
        "extracted": {},
        "tool_used": "",
        "assistant_message": "",
    }

    state_out = agent_app.invoke(state_in)

    updated_draft = state_out.get("draft", {}) or {}
    tool_used = state_out.get("tool_used", "DraftUpdate")
    assistant_message = state_out.get("assistant_message", "")

    # ---- Edit intent: execute edit immediately (no interaction_id in UI) ----
    if tool_used == "EditInteraction" and updated_draft.get("_edit_payload"):
        ep = updated_draft["_edit_payload"] or {}

        # ✅ fallback: if user didn't repeat the HCP name in edit message, use current draft hcp_name
        hcp_name_for_edit = ep.get("hcp_name") or updated_draft.get("hcp_name")
        hcp_id_for_edit = ep.get("hcp_id") or updated_draft.get("hcp_id")

        result = tool_edit_latest_interaction(
            db=db,
            hcp_id=hcp_id_for_edit,
            hcp_name=hcp_name_for_edit,
            fields_to_update=ep.get("fields_to_update") or {},
        )

        if "error" in result:
            assistant_message = result["error"]
        else:
            assistant_message = result.get("message", "Updated latest interaction.")
            updated_draft["_last_edited_interaction_id"] = result.get("interaction_id")

            # ✅ Refresh UI draft from latest DB record
            # Prefer hcp_id if available; else use hcp_name
            ctx = None
            hcp_id_for_ctx = result.get("hcp_id") or hcp_id_for_edit or updated_draft.get("hcp_id")

            if hcp_id_for_ctx:
                ctx = tool_retrieve_hcp_context(db, hcp_id=hcp_id_for_ctx, hcp_name=None)
            elif hcp_name_for_edit:
                ctx = tool_retrieve_hcp_context(db, hcp_id=None, hcp_name=hcp_name_for_edit)

            if ctx and "latest_interactions" in ctx and ctx["latest_interactions"]:
                latest = ctx["latest_interactions"][0]

                for k in [
                    "interaction_type", "date", "time", "attendees", "topics_discussed",
                    "materials_shared", "samples_distributed", "consent_required",
                    "occurred_at", "sentiment", "products_discussed", "summary", "outcomes", "follow_ups"
                ]:
                    if k in latest:
                        updated_draft[k] = latest[k]

        # cleanup so UI never shows internal payload
        updated_draft.pop("_edit_payload", None)

    return {
        "assistant_message": assistant_message,
        "updated_draft": updated_draft,
        "tool_used": tool_used,
    }


# ----------------------------
# Tool 1: Log Interaction (DB write)
# ----------------------------
@router.post("/tools/log")
def tools_log(draft: Dict[str, Any], db: Session = Depends(get_db)) -> Dict[str, Any]:
    result = tool_log_interaction(db, draft)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ----------------------------
# Tool 2: Edit Latest Interaction (no interaction_id)
# ----------------------------
@router.post("/tools/edit-latest")
def tools_edit_latest(payload: Dict[str, Any], db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    payload:
    {
      "hcp_id": 1 (optional),
      "hcp_name": "Dr. Asha Sharma" (optional),
      "fields_to_update": {...}
    }
    """
    fields = payload.get("fields_to_update") or {}
    if not fields:
        raise HTTPException(status_code=400, detail="fields_to_update is required")

    result = tool_edit_latest_interaction(
        db=db,
        hcp_id=payload.get("hcp_id"),
        hcp_name=payload.get("hcp_name"),
        fields_to_update=fields,
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ----------------------------
# Tool 3: Retrieve HCP Context
# ----------------------------
@router.get("/tools/hcp-context")
def tools_hcp_context(hcp_id: Optional[int] = None, hcp_name: Optional[str] = None, db: Session = Depends(get_db)) -> Dict[str, Any]:
    result = tool_retrieve_hcp_context(db, hcp_id=hcp_id, hcp_name=hcp_name)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ----------------------------
# Tool 4: Follow-up Suggestions
# ----------------------------
@router.post("/tools/followup-suggest")
def tools_followup_suggest(payload: Dict[str, Any]) -> Dict[str, Any]:
    draft = payload.get("draft") or {}
    context = payload.get("context") or None
    suggestions = tool_followup_suggestions(draft, context=context)
    return {"_ai_suggestions": suggestions}


# ----------------------------
# Tool 5: Compliance Check
# ----------------------------
@router.post("/tools/compliance-check")
def tools_compliance_check(payload: Dict[str, Any]) -> Dict[str, Any]:
    draft = payload.get("draft") or {}
    return {"_compliance": tool_compliance_check(draft)}
