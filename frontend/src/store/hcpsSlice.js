import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import axios from "axios";

const API = "http://localhost:8000";

export const fetchHcps = createAsyncThunk("hcps/fetch", async () => {
  const res = await axios.get(`${API}/hcps`);
  return res.data;
});

const hcpsSlice = createSlice({
  name: "hcps",
  initialState: { items: [], status: "idle", error: null },
  reducers: {},
  extraReducers: (b) => {
    b.addCase(fetchHcps.pending, (s) => { s.status = "loading"; })
     .addCase(fetchHcps.fulfilled, (s, a) => { s.status = "succeeded"; s.items = a.payload; })
     .addCase(fetchHcps.rejected, (s, a) => { s.status = "failed"; s.error = a.error.message; });
  },
});

export default hcpsSlice.reducer;
