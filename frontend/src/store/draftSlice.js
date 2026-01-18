// frontend/src/store/draftSlice.js
import { createSlice } from "@reduxjs/toolkit";

const initialDraft = {
  interaction_type: "Meeting",

  // video-style: no dropdown required; HCP name filled by AI
  hcp_name: "",

  date: "",
  time: "",
  attendees: "",
  topics_discussed: "",
  materials_shared: "",
  samples_distributed: "",
  consent_required: false,

  occurred_at: "",
  sentiment: "neutral",
  products_discussed: "",
  summary: "",
  outcomes: "",
  follow_ups: "",

  _ai_suggestions: [],
  _compliance: null,
};

const draftSlice = createSlice({
  name: "draft",
  initialState: { value: initialDraft },
  reducers: {
    setDraft: (state, action) => {
      state.value = action.payload; // IMPORTANT
    },
    setField: (state, action) => {
      const { key, value } = action.payload;
      state.value[key] = value;
    },
    resetDraft: (state) => {
      state.value = initialDraft;
    },
  },
});

export const { setDraft, setField, resetDraft } = draftSlice.actions;
export default draftSlice.reducer;
