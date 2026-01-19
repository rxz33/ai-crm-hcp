import { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import axios from "axios";
import { setDraft, resetDraft } from "../store/draftSlice";
import { addMessage, setLoading, setLastToolUsed, resetChat } from "../store/chatSlice";

const API = "http://localhost:8000";
const FORM_LOCKED = true;

function Field({ label, children }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      <div style={{fontWeight: 700, color: "#374151" }}>{label}</div>
      {children}
    </div>
  );
}

function Input({ disabled, style, ...props }) {
  return (
    <input
      {...props}
      disabled={disabled}
      style={{
        padding: "10px 12px", 
        borderRadius: 10,
        fontFamily: "inherit",
        fontSize: "inherit",
        border: "1px solid #dfe3ea",
        outline: "none",
        background: disabled ? "#f3f4f6" : "white",
        color: disabled ? "#000000" : "#111827",
        cursor: disabled ? "not-allowed" : "text",
        ...style,
      }}
    />
  );
}

function TextArea({ disabled, style, ...props }) {
  return (
    <textarea
      {...props}
      disabled={disabled}
      style={{
        padding: "10px 12px",
        borderRadius: 10,
        fontFamily: "inherit",
        fontSize: "inherit",
        border: "1px solid #dfe3ea",
        outline: "none",
        background: disabled ? "#f3f4f6" : "white",
        color: disabled ? "#000000" : "#111827",
        minHeight: 80,
        resize: "vertical",
        cursor: disabled ? "not-allowed" : "text",
        ...style,
      }}
    />
  );
}

function Card({ title, right, children }) {
  return (
    <div
      style={{
        background: "white",
        fontFamily: "inherit",
        border: "1px solid #e7eaf0",
        borderRadius: 16,
        padding: 16,
        boxShadow: "0 6px 18px rgba(16,24,40,0.06)",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <div style={{fontSize: "15", fontWeight: 800 }}>{title}</div>
        {right}
      </div>
      {children}
    </div>
  );
}

function Button({ children, onClick, disabled, variant = "primary", style }) {
  const bg = variant === "primary" ? "#111827" : "#ffffff";
  const color = variant === "primary" ? "#ffffff" : "#111827";
  const border = variant === "primary" ? "1px solid #111827" : "1px solid #d1d5db";
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        padding: "10px 12px",
        borderRadius: 12,
        border,
        background: disabled ? "#9ca3af" : bg,
        color,
        cursor: disabled ? "not-allowed" : "pointer",
        fontWeight: 700,
        ...style,
      }}
    >
      {children}
    </button>
  );
}

export default function LogInteractionPage() {
  const dispatch = useDispatch();
  const draft = useSelector((s) => s.draft.value);
  const chat = useSelector((s) => s.chat);

  const [chatInput, setChatInput] = useState("");
  const [hcpContext, setHcpContext] = useState(null);

  function resetAll() {
    dispatch(resetDraft());
    dispatch(resetChat());
    setChatInput("");
  }

  async function toolHcpContextFrontend() {
    const name = (draft.hcp_name || "").trim();
    if (!name) {
      dispatch(addMessage({ role: "assistant", content: "Please mention the HCP name in chat first (e.g., Dr. Asha Sharma)." }));
      return;
    }

    try {
      const res = await axios.get(`${API}/agent/tools/hcp-context`, {
        params: { hcp_name: name },
      });

      setHcpContext(res.data);

      const latest = res.data?.latest_interactions?.[0];
      dispatch(
        addMessage({
          role: "assistant",
          content: latest
            ? `📌 Context loaded. Latest interaction: sentiment=${latest.sentiment}, products=${latest.products_discussed || "-"}, follow_ups=${latest.follow_ups || "-"}`
            : "📌 Context loaded. No interactions found yet.",
        })
      );

      dispatch(setLastToolUsed("RetrieveHCPContextTool"));
    } catch (e) {
      dispatch(addMessage({ role: "assistant", content: "❌ Context fetch failed. Check backend or HCP name." }));
    }
  }

  async function sendChat() {
    const msg = chatInput.trim();
    if (!msg) return;

    dispatch(addMessage({ role: "user", content: msg }));
    dispatch(setLoading(true));
    setChatInput("");

    try {
      const res = await axios.post(`${API}/agent/chat`, {
        mode: "draft",
        message: msg,
        draft: draft,
      });

      dispatch(setDraft(res.data.updated_draft));
      dispatch(setLastToolUsed(res.data.tool_used));
      dispatch(addMessage({ role: "assistant", content: res.data.assistant_message }));
    } catch (e) {
      dispatch(addMessage({ role: "assistant", content: "❌ Backend error. Is FastAPI running on :8000?" }));
    } finally {
      dispatch(setLoading(false));
    }
  }

  function formatTimeAmPm(t) {
  if (!t) return "";
  const s = String(t).trim();

  // If already contains AM/PM, return as-is
  if (/am|pm/i.test(s)) return s;

  // Expect "HH:MM"
  const m = s.match(/^(\d{1,2}):(\d{2})$/);
  if (!m) return s;

  let h = parseInt(m[1], 10);
  const min = m[2];
  const ampm = h >= 12 ? "PM" : "AM";
  h = h % 12;
  if (h === 0) h = 12;

  return `${h}:${min} ${ampm}`;
}


  async function logInteraction() {
    if (!draft.hcp_name) {
      dispatch(addMessage({ role: "assistant", content: "Please mention the HCP name in chat before logging." }));
      return;
    }

    try {
      const res = await axios.post(`${API}/agent/tools/log`, draft);
      dispatch(addMessage({ role: "assistant", content: `✅ Logged successfully.` }));
      dispatch(setLastToolUsed("LogInteraction"));
      // optional: store last logged id in draft (for debugging only)
      dispatch(setDraft({ ...draft, _last_logged_interaction_id: res.data.interaction_id }));
    } catch (e) {
      dispatch(addMessage({ role: "assistant", content: `❌ Log failed: ${e?.response?.data?.detail || "unknown error"}` }));
    }
  }

  return (
    <div style={{ padding: 20, maxWidth: 1200, margin: "0 auto" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <div>
          <div style={{ fontSize: 22, fontWeight: 900, color: "#111827" }}>Log HCP Interaction</div>
          <div style={{ fontSize: 13, color: "#6b7280" }}>
            {/* Form + AI Assistant (LangGraph + Groq) */}
          </div>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <Button variant="secondary" onClick={resetAll}>Reset Log</Button>
          <Button onClick={logInteraction} disabled={!draft.hcp_name}>Log</Button>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1.15fr 0.85fr", gap: 16 }}>
        {/* LEFT (LOCKED FORM) */}
        <Card
          title="Interaction Details"
          right={<div style={{ fontSize: 15, color: "#6b7280" }}>Selected: {draft.hcp_name || "—"}</div>}
        >
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <Field label="HCP Name">
              <Input disabled value={draft.hcp_name || ""} placeholder="Required HCP Name" />
            </Field>

            <Field label="Interaction Type">
              <Input disabled={FORM_LOCKED} value={draft.interaction_type || "Meeting"} />
            </Field>

            <Field label="Date">
              <Input disabled value={draft.date || ""} placeholder="YYYY-MM-DD" />
            </Field>

            <Field label="Time">
              {/* <Input disabled value={draft.time || ""} placeholder="HH:MM" /> */}
              <Input disabled value={formatTimeAmPm(draft.time || "")} placeholder="--:--" />
            </Field>

            <div style={{ gridColumn: "1 / -1" }}>
              <Field label="Attendees">
                <Input disabled value={draft.attendees || ""} placeholder="Enter names" />
              </Field>
            </div>

            <div style={{ gridColumn: "1 / -1" }}>
              <Field label="Topics Discussed">
                <TextArea disabled value={draft.topics_discussed || ""} placeholder="Enter key discussion points..." />
              </Field>
            </div>

            <Field label="Sentiment">
              <Input disabled value={draft.sentiment || "neutral"} />
            </Field>

            <Field label="Products Discussed">
              <Input disabled value={draft.products_discussed || ""} />
            </Field>

            <div style={{ gridColumn: "1 / -1" }}>
              <Field label="Materials Shared">
                <Input disabled value={draft.materials_shared || ""} />
              </Field>
            </div>

            <div style={{ gridColumn: "1 / -1" }}>
              <Field label="Samples Distributed">
                <Input disabled value={draft.samples_distributed || ""} />
              </Field>
            </div>

            <div style={{ gridColumn: "1 / -1" }}>
              <Field label="Summary">
                <TextArea disabled value={draft.summary|| ""} />
              </Field>
            </div>

            <div style={{ gridColumn: "1 / -1" }}>
              <Field label="Outcomes">
                <TextArea disabled value={draft.outcomes|| ""} />
              </Field>
            </div>

            <div style={{ gridColumn: "1 / -1" }}>
              <Field label="Follow-up Actions">
                <TextArea disabled value={draft.follow_ups|| ""} />
              </Field>
            </div>

            <div style={{ gridColumn: "1 / -1" }}>
  <Field label="AI Suggestions:">
    {draft._ai_suggestions?.length ? (
      <ul style={{ margin: 0, paddingLeft: 18,fontSize: "15px",fontFamily: "Google Inter" }}>
        {draft._ai_suggestions.map((s, i) => (
          <li key={i} style={{ marginBottom: 6, color: "#374151", fontWeight: 50, font:"Google-Inter" }}>
            {s}
          </li>
        ))}
      </ul>
    ) : (
      <div style={{ color: "#6b7280", fontWeight: 300 }}>—</div>
    )}
  </Field>
</div>

          </div>

          {/* <div style={{ marginTop: 14 }}>
            <div
              style={{
                marginTop: 6,
                fontSize: 12,
                color: draft._compliance?.status === "ok" ? "#059669" : "#b45309",
              }}
            >
              Compliance:{" "}
              {draft._compliance
                ? `${draft._compliance.status}${draft._compliance.issues?.length ? " • " + draft._compliance.issues.join(" | ") : ""}`
                : "—"}
            </div>
          </div> */}

          <div style={{ marginTop: 14 }}>
          <div style={{fontWeight: 600, color: "#059669", marginBottom: 6 }}>
            Compliance:
          </div>

  {draft._compliance ? (
    <div>
      <div
        style={{
          display: "inline-block",
          fontWeight: 800,
          padding: "6px 10px",
          borderRadius: 999,
          border: "1px solid",
          borderColor: draft._compliance.status === "ok" ? "#bbf7d0" : "#fed7aa",
          background: draft._compliance.status === "ok" ? "#dcfce7" : "#ffedd5",
          color: "#111827",
          marginBottom: 8,
        }}
      >
        {draft._compliance.status.toUpperCase()}
      </div>

      {draft._compliance.issues?.length ? (
        <ul style={{ margin: 0, paddingLeft: 18 }}>
          {draft._compliance.issues.map((issue, i) => (
            <li key={i} style={{ marginBottom: 6,fontWeight: 600, color: "#b45309" }}>
              {issue}
            </li>
          ))}
        </ul>
      ) : (
        <div style={{fontWeight: 600, color: "#374151" }}>No issues found.</div>
      )}
    </div>
  ) : (
    <div style={{fontWeight: 600, color: "#374151" }}>—</div>
  )}
</div>


        </Card>

        {/* RIGHT (CHAT ONLY) */}
        <Card title="AI Assistant" right={<div style={{ fontSize: 15, color: "#6b7280" }}>Last: {chat.lastToolUsed || "—"}</div>}>
          <div
            style={{
              border: "1px solid #e5e7eb",
              background: "#f8fafc",
              padding: 12,
              fontSize: 14, 
              borderRadius: 12,
              color: "#374151",
              marginBottom: 12,
            }}
          >
            Describe what happened with the HCP. I’ll fill the form fields and suggest follow-ups.
            <br />
            Try: “Met Dr. Asha Sharma today. Discussed CardioPlus. Shared brochure. Positive.”
          </div>

          <div
            style={{
              height: 420,
              overflow: "auto",
              border: "1px solid #eef0f5",
              borderRadius: 14,
              fontSize: 14,
              padding: 12,
              background: "#fbfcff",
              display: "flex",
              flexDirection: "column",
              gap: 10,
            }}
          >
            {chat.messages.map((m, idx) => (
              <div
                key={idx}
                style={{
                  alignSelf: m.role === "user" ? "flex-end" : "flex-start",
                  maxWidth: "85%",
                  background: m.role === "user" ? "#111827" : "white",
                  color: m.role === "user" ? "white" : "#111827",
                  border: m.role === "user" ? "1px solid #111827" : "1px solid #e6e9f0",
                  padding: "10px 12px",
                  borderRadius: 14,
                  fontSize: 14,
                  whiteSpace: "pre-wrap",
                }}
              >
                {m.content}
              </div>
            ))}
            {chat.loading && <div style={{ fontSize: 12, color: "#6b7280" }}>Thinking…</div>}
          </div>

          <div style={{ display: "flex", gap: 10, marginTop: 12 }}>
            <Input
              disabled={chat.loading}
              placeholder="Type your interaction note..."
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") sendChat();
              }}
              style={{ flex: 1 }}
            />
            <Button onClick={sendChat} disabled={chat.loading}>Send</Button>
          </div>

          <div style={{ marginTop: 10, fontSize: 13, color: "#6b7280" }}>
            Corrections example: “Sorry, sentiment is negative and follow-up is send brochure tomorrow.”
          </div>

          {hcpContext && (
  <div
    style={{
      marginTop: 12,
      border: "1px solid #e5e7eb",
      borderRadius: 12,
      padding: 12,
      background: "#fff",
    }}
  >
    <div style={{ fontWeight: 700, marginBottom: 8 }}>HCP Context</div>

    <div style={{ fontSize: 13, color: "#111827" }}>
      <div><b>Name:</b> {hcpContext.hcp?.name}</div>
      {/* <div><b>Specialty:</b> {hcpContext.hcp?.specialty || "-"}</div>
      <div><b>City:</b> {hcpContext.hcp?.city || "-"}</div> */}
    </div>

    <div style={{ marginTop: 10, fontWeight: 600 }}>Recent Interactions</div>
    <ul style={{ marginTop: 6, paddingLeft: 18, fontSize: 13, color: "#111827" }}>
      {(hcpContext.latest_interactions || []).map((i) => (
        <li key={i.id}>
          #{i.id} • {i.created_at} • {i.sentiment} • {i.products_discussed || "-"} • {i.follow_ups || "-"}
        </li>
      ))}
    </ul>
  </div>
)}


          <div style={{ marginTop: 12 }}>
          <Button variant="secondary" onClick={toolHcpContextFrontend} disabled={!draft.hcp_name}>
            Tool: Retrieve HCP Context
          </Button>
          </div>
        </Card>
      </div>
    </div>
  );
}
