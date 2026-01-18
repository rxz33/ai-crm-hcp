from typing import Any, Dict, TypedDict, Optional

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage

from app.services.groq_client import get_llm
from app.agent.prompts import SYSTEM_PROMPT
from app.agent.utils import merge_json_safely
from app.agent.tools import tool_followup_suggestions, tool_compliance_check

from datetime import datetime
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

class AgentState(TypedDict):
    message: str
    mode: str

    # Draft is the single source of truth the UI renders (left form is read-only)
    draft: Dict[str, Any]

    # LLM extraction raw + parsed
    extracted: Dict[str, Any]

    # UI outputs
    tool_used: str
    assistant_message: str


llm = get_llm()


# ----------------------------
# Node 1: Extract (LLM -> JSON)
# ----------------------------
def extract_node(state: AgentState) -> AgentState:
    prompt = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=(
                "User message:\n"
                f"{state.get('message','')}\n\n"
                "Current draft JSON:\n"
                f"{state.get('draft', {})}\n\n"
                "Return ONLY JSON."
            )
        ),
    ]
    resp = llm.invoke(prompt)
    raw = (resp.content or "").strip()

    parsed = merge_json_safely(raw)

    state["extracted"] = {"raw": raw, "parsed": parsed}
    state["tool_used"] = "Extract"
    state["assistant_message"] = "Noted."
    return state


# ----------------------------
# Helper: Merge parsed into draft
# ----------------------------
def merge_into_draft(draft: Dict[str, Any], parsed: Dict[str, Any]) -> Dict[str, Any]:
    # Remove routing keys that shouldn't be merged directly
    parsed = dict(parsed or {})
    parsed.pop("action", None)
    parsed.pop("fields_to_update", None)

    # Only merge non-empty values
    for k, v in parsed.items():
        if v is None:
            continue
        if isinstance(v, str) and v.strip() == "":
            continue
        draft[k] = v
    return draft


# ----------------------------
# Node 2: Draft Update (merge + suggestions + compliance)
# ----------------------------
def draft_update_node(state: AgentState) -> AgentState:
    parsed = state.get("extracted", {}).get("parsed", {}) or {}
    draft = state.get("draft", {}) or {}

    # 1️⃣ Merge model output into draft
    draft = merge_into_draft(draft, parsed)
    
    name = str(draft.get("hcp_name", "")).strip()
    if name and not name.lower().startswith("dr"):
        draft["hcp_name"] = f"Dr. {name}"

    # Helper: current datetime
    def _now():
        if ZoneInfo:
            return datetime.now(ZoneInfo("Asia/Kolkata"))
        return datetime.now()

    # 2️⃣ Normalize date EARLY (handle "today", "today at ...", etc.)
    raw_date = str(draft.get("date", "")).strip().lower()
    if raw_date.startswith("today") or raw_date in ["now", "todays", "today's"]:
        draft["date"] = _now().strftime("%Y-%m-%d")

    # 3️⃣ If date still missing, auto-fill today
    if not draft.get("date"):
        draft["date"] = _now().strftime("%Y-%m-%d")

    # 4️⃣ Time convenience mapping
    if (not draft.get("time")) and draft.get("occurred_at"):
        occ = str(draft.get("occurred_at"))
        if len(occ) <= 8:  # "16:30" or "4:30 PM"
            draft["time"] = occ

    # 5️⃣ Suggestions + compliance
    draft["_ai_suggestions"] = tool_followup_suggestions(draft)
    draft["_compliance"] = tool_compliance_check(draft)

    # 6️⃣ Update state
    state["draft"] = draft
    state["tool_used"] = "DraftUpdate"

    # 7️⃣ Assistant message
    if not draft.get("hcp_id") and not draft.get("hcp_name"):
        state["assistant_message"] = (
            "Draft updated. Please mention the HCP name (e.g., 'Met Dr. Asha Sharma...') so I can log it."
        )
    else:
        state["assistant_message"] = "Draft updated. Say 'log it' to save, or send a correction to edit."

    return state

# ----------------------------
# Node 3: Edit intent packaging (no DB write here)
# ----------------------------
def edit_intent_node(state: AgentState) -> AgentState:
    parsed = state.get("extracted", {}).get("parsed", {}) or {}
    draft = state.get("draft", {}) or {}

    # We store the edit payload inside draft for the API layer to execute:
    # - hcp_name/hcp_id can come from parsed or existing draft
    # - fields_to_update comes from parsed
    fields_to_update = parsed.get("fields_to_update") or {}

    draft["_edit_payload"] = {
        "hcp_id": parsed.get("hcp_id") or draft.get("hcp_id"),
        "hcp_name": parsed.get("hcp_name") or draft.get("hcp_name"),
        "fields_to_update": fields_to_update,
    }

    # Also merge any extracted regular fields into draft for UI display
    draft = merge_into_draft(draft, parsed)

    # Update suggestions/compliance for UI preview
    draft["_ai_suggestions"] = tool_followup_suggestions(draft)
    draft["_compliance"] = tool_compliance_check(draft)

    state["draft"] = draft
    state["tool_used"] = "EditInteraction"
    state["assistant_message"] = "Edit request captured. Say 'apply edit' or click Edit in backend flow."
    return state


# ----------------------------
# Node 4: Log intent packaging (no DB write here)
# ----------------------------
def log_intent_node(state: AgentState) -> AgentState:
    parsed = state.get("extracted", {}).get("parsed", {}) or {}
    draft = state.get("draft", {}) or {}

    # Merge extracted fields in case message contains missing bits
    draft = merge_into_draft(draft, parsed)

    # suggestions/compliance for UI
    draft["_ai_suggestions"] = tool_followup_suggestions(draft)
    draft["_compliance"] = tool_compliance_check(draft)

    state["draft"] = draft
    state["tool_used"] = "LogInteraction"
    state["assistant_message"] = "Ready to log. Logging will happen via the Log tool endpoint."
    return state


# ----------------------------
# Router: decide which path to take
# ----------------------------
def decide_node(state: AgentState) -> str:
    parsed = state.get("extracted", {}).get("parsed", {}) or {}
    action = (parsed.get("action") or "draft").lower()

    if action == "edit":
        return "edit"
    if action == "log":
        return "log"
    return "draft"


# ----------------------------
# Build graph
# ----------------------------
def build_graph():
    g = StateGraph(AgentState)

    g.add_node("extract", extract_node)
    g.add_node("draft_update", draft_update_node)
    g.add_node("edit_intent", edit_intent_node)
    g.add_node("log_intent", log_intent_node)

    g.set_entry_point("extract")

    g.add_conditional_edges(
        "extract",
        decide_node,
        {
            "draft": "draft_update",
            "edit": "edit_intent",
            "log": "log_intent",
        },
    )

    g.add_edge("draft_update", END)
    g.add_edge("edit_intent", END)
    g.add_edge("log_intent", END)

    return g.compile()


agent_app = build_graph()
