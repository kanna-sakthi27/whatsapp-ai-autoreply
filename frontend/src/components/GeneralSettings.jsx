import React, { useState, useEffect } from "react"
import {
  Box, TextField, Button, Typography, Paper, Alert
} from "@mui/material"
import { Save as SaveIcon } from "@mui/icons-material"
import client from "../api/client"
import { useApp } from "../App"

export default function GeneralSettings() {
  const [settings, setSettings] = useState({
    waha_base_url: "http://waha:3000",
    max_conversation_history: 50,
    default_language: "en",
    log_level: "INFO",
    auto_reply: true
  })
  const [saving, setSaving] = useState(false)
  const { addToast } = useApp()

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await client.get("/settings")
        if (res.data) setSettings(res.data)
      } catch {}
    }
    fetch()
  }, [])

  const handleSave = async () => {
    setSaving(true)
    try {
      await client.put("/settings", settings)
      addToast("Settings saved", "success")
    } catch (err) {
      addToast("Save failed: " + err.message, "error")
    } finally { setSaving(false) }
  }

  return (
    <div className="page-card">
      <Box sx={{ display: "flex", flexDirection: "column", gap: 3, maxWidth: 600 }}>
        <TextField
          label="WAHA Base URL"
          value={settings.waha_base_url || ""}
          onChange={(e) => setSettings({ ...settings, waha_base_url: e.target.value })}
          fullWidth
          variant="outlined"
          placeholder="http://waha:3000"
          sx={{ "& .MuiOutlinedInput-root": { background: "rgba(0,0,0,0.2)" } }}
        />
        <TextField
          label="Max Conversation History"
          type="number"
          value={settings.max_conversation_history || 50}
          onChange={(e) => setSettings({ ...settings, max_conversation_history: parseInt(e.target.value) || 50 })}
          fullWidth
          variant="outlined"
          sx={{ "& .MuiOutlinedInput-root": { background: "rgba(0,0,0,0.2)" } }}
        />
        <TextField
          label="Default Language"
          value={settings.default_language || "en"}
          onChange={(e) => setSettings({ ...settings, default_language: e.target.value })}
          fullWidth
          variant="outlined"
          sx={{ "& .MuiOutlinedInput-root": { background: "rgba(0,0,0,0.2)" } }}
        />
        <TextField
          label="Log Level"
          value={settings.log_level || "INFO"}
          onChange={(e) => setSettings({ ...settings, log_level: e.target.value })}
          fullWidth
          variant="outlined"
          sx={{ "& .MuiOutlinedInput-root": { background: "rgba(0,0,0,0.2)" } }}
        />
        <Button
          variant="contained"
          onClick={handleSave}
          disabled={saving}
          startIcon={<SaveIcon />}
          sx={{ background: "linear-gradient(135deg, #7c4dff, #00e5ff)" }}
        >
          {saving ? "Saving..." : "Save Settings"}
        </Button>
      </Box>
    </div>
  )
}
