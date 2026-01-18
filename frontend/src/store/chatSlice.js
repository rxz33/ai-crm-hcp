import { createSlice } from "@reduxjs/toolkit";

const chatSlice = createSlice({
  name: "chat",
  initialState: {
    messages: [
      { role: "assistant", content: "Hi! Describe your HCP interaction and I’ll fill the CRM draft for you." },
    ],
    lastToolUsed: "",
    loading: false,
  },
  reducers: {
    addMessage: (state, action) => {
      state.messages.push(action.payload);
    },
    setLoading: (state, action) => {
      state.loading = action.payload;
    },
    setLastToolUsed: (state, action) => {
      state.lastToolUsed = action.payload;
    },
    resetChat: (state) => {
      state.messages = [
        { role: "assistant", content: "Hi! Describe your HCP interaction and I’ll fill the CRM draft for you." },
      ];
      state.lastToolUsed = "";
      state.loading = false;
    },
  },
});

export const { addMessage, setLoading, setLastToolUsed, resetChat } = chatSlice.actions;
export default chatSlice.reducer;
