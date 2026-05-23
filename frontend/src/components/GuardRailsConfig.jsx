import React, { useState, useEffect } from "react"
import {
  Box, TextField, Button, Switch, FormControlLabel, Typography,
  Chip, Slider, Alert, Paper
} from "@mui/material"
import { Save as SaveIcon } from "@mui/icons-material"
import client from "../api/client"
import { useApp } from "../App"

export default function GuardRailsConfig() {
  const [config, setConfig] = useState({
    profanity_filter: true, pii_detection: true, topic_blacklist: true,
    approval_mode: false, rate_limit: true, max_message_length: 500,
    max_requests_per_minute: 10, blocked_words: "", blocked_topics: ""
  })
  const [saving, setSaving] = useState(false)
  const { addToast } = useApp()

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await client.get("/settings/guardrails")
        if (res.data) setConfig(res.data)
      } catch {}
    }
    fetch()
  }, [])

  const handleSave = async () => {
    setSaving(true)
    try {
      await client.put("/settings/guardrails", config)
      addToast("Guard rails config saved", "success")
    } catch (err) {
      addToast("Save failed: " + err.message, "error")
    } finally { setSaving(false) }
  }

  return (
    <div className="page-card">
      <Box sx={{ display: "flex", flexDirection: "column", gap: 3, maxWidth: 600 }}>
        <Paper sx={{ p: 3, background: "rgba(0,0,0,0.2)" }}>
          <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 600 }}>Filters</Typography>
          <FormControlLabel
            control={<Switch checked={config.profanity_filter} onChange={(e) => setConfig({ ...config, profanity_filter: e.target.checked })} />}
            label="Profanity Filter"
            sx={{ color: "rgba(255,255,255,0.7)" }}
          />
          <FormControlLabel
            control={<Switch checked={config.pii_detection} onChange={(e) => setConfig({ ...config, pii_detection: e.target.checked })} />}
            label="PII Detection"
            sx={{ color: "rgba(255,255,255,0.7)" }}
          />
          <FormControlLabel
            control={<Switch checked={config.topic_blacklist} onChange={(e) => setConfig({ ...config, topic_blacklist: e.target.checked })} />}
            label="Topic Blacklist"
            sx={{ color: "rgba(255,255,255,0.7)" }}
          />
          <FormControlLabel
            control={<Switch checked={config.rate_limit} onChange={(e) => setConfig({ ...config, rate_limit: e.target.checked })} />}
            label="Rate Limiting"
            sx={{ color: "rgba(255,255,255,0.7)" }}
          />
        </Paper>

        <Paper sx={{ p: 3, background: "rgba(0,0,0,0.2)" }}>
          <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 600 }}>Approval Mode</Typography>
          <FormControlLabel
            control={<Switch checked={config.approval_mode} onChange={(e) => setConfig({ ...config, approval_mode: e.target.checked })} />}
            label="Require approval for all outgoing messages"
            sx={{ color: "rgba(255,255,255,0.7)" }}
          />
        </Paper>

        <Paper sx={{ p: 3, background: "rgba(0,0,0,0.2)" }}>
          <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 600 }}>Limits</Typography>
          <Typography variant="body2" sx={{ color: "rgba(255,255,255,0.5)", mb: 1 }}>
            Max Message Length: {config.max_message_length || 500} chars
          </Typography>
          <Slider
            value={config.max_message_length || 500}
            onChange={(e, val) => setConfig({ ...config, max_message_length: val })}
            min={100}
            max={2000}
            step={50}
            sx={{ color: "#7c4dff" }}
          />
          <Typography variant="body2" sx={{ color: "rgba(255,255,255,0.5)", mt: 2, mb: 1 }}>
            Max Requests/Minute: {config.max_requests_per_minute || 10}
          </Typography>
          <Slider
            value={config.max_requests_per_minute || 10}
            onChange={(e, val) => setConfig({ ...config, max_requests_per_minute: val })}
            min={1}
            max={100}
            sx={{ color: "#7c4dff" }}
          />
        </Paper>

        <TextField
          label="Blocked Words (comma separated)"
          value={config.blocked_words || ""}
          onChange={(e) => setConfig({ ...config, blocked_words: e.target.value })}
          multiline rows={2}
          fullWidth
          variant="outlined"
          sx={{ "& .MuiOutlinedInput-root": { background: "rgba(0,0,0,0.2)" } }}
        />

        <TextField
          label="Blocked Topics (comma separated)"
          value={config.blocked_topics || ""}
          onChange={(e) => setConfig({ ...config, blocked_topics: e.target.value })}
          multiline rows={2}
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
          {saving ? "Saving..." : "Save Configuration"}
        </Button>
      </Box>
    </div>
  )
}
