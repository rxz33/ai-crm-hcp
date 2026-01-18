from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class HCPOut(BaseModel):
    id: int
    name: str
    specialty: str
    city: str
    class Config:
        from_attributes = True

class InteractionBase(BaseModel):
    hcp_id: int
    interaction_type: str = "Visit"

    date: str = ""
    time: str = ""
    attendees: str = ""
    topics_discussed: str = ""
    materials_shared: str = ""
    samples_distributed: str = ""
    consent_required: bool = False

    occurred_at: str = ""
    sentiment: str = "neutral"
    products_discussed: str = ""
    summary: str = ""
    outcomes: str = ""
    follow_ups: str = ""

class InteractionCreate(InteractionBase):
    pass

class InteractionOut(InteractionBase):
    id: int
    created_at: Optional[str] = None
    class Config:
        from_attributes = True

class AgentChatIn(BaseModel):
    mode: str = Field(default="draft", description="draft or save")
    message: str
    draft: Dict[str, Any] = Field(default_factory=dict)

class AgentChatOut(BaseModel):
    assistant_message: str
    updated_draft: Dict[str, Any]
    tool_used: str
