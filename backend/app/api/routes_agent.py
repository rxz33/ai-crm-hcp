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
    """
    Expected payload:
    {
      "mode": "draft",
      "message": "...",
      "draft": {...}
    }
    """
    message = (payload.get("message") or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="message is required")

    draft = payload.get("draft") or {}

    # Run graph: it extracts/merges and sets tool_used + assistant_message
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

    # If graph captured edit intent, optionally execute edit immediately
    # (chat-only UX: user says sorry/change, backend edits without interaction_id)
    if tool_used == "EditInteraction" and updated_draft.get("_edit_payload"):
        ep = updated_draft["_edit_payload"]
        result = tool_edit_latest_interaction(
            db=db,
            hcp_id=ep.get("hcp_id"),
            hcp_name=ep.get("hcp_name"),
            fields_to_update=ep.get("fields_to_update") or {},
        )
        if "error" in result:
            assistant_message = result["error"]
        else:
            assistant_message = result["message"]
            updated_draft["_last_edited_interaction_id"] = result["interaction_id"]
            
            # ✅ Refresh the UI draft from latest DB record
        hcp_id_for_ctx = result.get("hcp_id") or updated_draft.get("hcp_id")

        # if we still don't have hcp_id, resolve via name from draft
        if not hcp_id_for_ctx and updated_draft.get("hcp_name"):
    # resolve HCP by name (tool already has helper internally; easiest is call context by name)
            ctx = tool_retrieve_hcp_context(db, hcp_id=None, hcp_name=updated_draft.get("hcp_name"))
        else:
            ctx = tool_retrieve_hcp_context(db, hcp_id=hcp_id_for_ctx, hcp_name=None)

        if "latest_interactions" in ctx and ctx["latest_interactions"]:
            latest = ctx["latest_interactions"][0]

            # overwrite draft fields from DB
            for k in [
                "interaction_type","date","time","attendees","topics_discussed",
                "materials_shared","samples_distributed","consent_required",
                "occurred_at","sentiment","products_discussed","summary","outcomes","follow_ups"
            ]:
                if k in latest:
                    updated_draft[k] = latest[k]


        # cleanup internal payload so UI doesn't show it
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
