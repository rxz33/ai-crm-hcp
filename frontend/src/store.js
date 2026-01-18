import { configureStore } from "@reduxjs/toolkit";
import hcpsReducer from "./store/hcpsSlice";
import draftReducer from "./store/draftSlice";
import chatReducer from "./store/chatSlice";

export const store = configureStore({
  reducer: {
    hcps: hcpsReducer,
    draft: draftReducer,
    chat: chatReducer,
  },
});
