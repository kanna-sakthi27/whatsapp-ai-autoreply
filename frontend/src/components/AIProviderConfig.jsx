import React, { useState, useEffect } from "react"
import {
  Box, TextField, Button, Select, MenuItem, FormControl, InputLabel,
  Alert, Chip, Typography, IconButton, InputAdornment
} from "@mui/material"
import { Save as SaveIcon, PlayArrow as TestIcon, Visibility, VisibilityOff } from "@mui/icons-material"
import client from "../api/client"
import { useApp } from "../App"

const PROVIDERS = [
  { id: "ollama", label: "Ollama", models: ["llama3.2:1b", "llama3.1:8b", "mistral", "gemma2"] },
  { id: "openai", label: "OpenAI", models: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"] },
  { id: "anthropic", label: "Anthropic", models: ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"] },
  { id: "google", label: "Google", models: ["gemini-pro", "gemini-1.5-pro", "gemini-1.5-flash"] },
  { id: "groq", label: "Groq", models: ["llama3-70b", "llama3-8b", "mixtral-8x7b"] },
  { id: "cohere", label: "Cohere", models: ["command-r", "command-r-plus", "command-light"] },
  { id: "mistral", label: "Mistral", models: ["mistral-large", "mistral-medium", "mistral-small"] },
  { id: "together", label: "Together", models: ["llama-3.1-70b", "llama-3.1-8b", "mixtral-8x22b"] },
  { id: "deepseek", label: "DeepSeek", models: ["deepseek-chat", "deepseek-coder"] },
  { id: "perplexity", label: "Perplexity", models: ["llama-3.1-sonar-70b", "llama-3.1-sonar-8b"] },
  { id: "openrouter", label: "OpenRouter", models: ["auto", "anthropic/claude-3-opus", "openai/gpt-4o"] },
]

export default function AIProviderConfig() {
  const [config, setConfig] = useState({ provider: "ollama", model: "llama3.2:1b", api_key: "", base_url: "" })
  const [showKey, setShowKey] = useState(false)
  const [testResult, setTestResult] = useState(null)
  const [testing, setTesting] = useState(false)
  const [saving, setSaving] = useState(false)
  const { addToast } = useApp()

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const res = await client.get("/settings/ai")
        if (res.data) setConfig(res.data)
      } catch {}
    }
    fetchConfig()
  }, [])

  const selectedProvider = PROVIDERS.find(p => p.id === config.provider)
  const availableModels = selectedProvider ? selectedProvider.models : [config.model]

  const handleSave = async () => {
    setSaving(true)
    try {
      await client.put("/settings/ai", config)
      addToast("AI provider config saved", "success")
    } catch (err) {
      addToast("Save failed: " + err.message, "error")
    } finally { setSaving(false) }
  }

  const handleTest = async () => {
    setTesting(true)
    setTestResult(null)
    try {
      const res = await client.post("/settings/ai/test", config)
      setTestResult({ success: true, data: res.data })
      addToast("Connection successful!", "success")
    } catch (err) {
      setTestResult({ success: false, error: err.message })
      addToast("Test failed: " + err.message, "error")
    } finally { setTesting(false) }
  }

  return (
    <div className="page-card">
      <Box sx={{ display: "flex", flexDirection: "column", gap: 3, maxWidth: 600 }}>
        <FormControl fullWidth variant="outlined" sx={{ "& .MuiOutlinedInput-root": { background: "rgba(0,0,0,0.2)" } }}>
          <InputLabel>Provider</InputLabel>
          <Select
            value={config.provider}
            label="Provider"
            onChange={(e) => setConfig({ ...config, provider: e.target.value, model: (PROVIDERS.find(p => p.id === e.target.value)?.models || [config.model])[0] })}
          >
            {PROVIDERS.map(p => (
              <MenuItem key={p.id} value={p.id}>{p.label}</MenuItem>
            ))}
          </Select>
        </FormControl>

        <FormControl fullWidth variant="outlined" sx={{ "& .MuiOutlinedInput-root": { background: "rgba(0,0,0,0.2)" } }}>
          <InputLabel>Model</InputLabel>
          <Select
            value={config.model}
            label="Model"
            onChange={(e) => setConfig({ ...config, model: e.target.value })}
          >
            {availableModels.map(m => (
              <MenuItem key={m} value={m}>{m}</MenuItem>
            ))}
          </Select>
        </FormControl>

        <TextField
          label="API Key"
          type={showKey ? "text" : "password"}
          value={config.api_key || ""}
          onChange={(e) => setConfig({ ...config, api_key: e.target.value })}
          fullWidth
          variant="outlined"
          sx={{ "& .MuiOutlinedInput-root": { background: "rgba(0,0,0,0.2)" } }}
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton onClick={() => setShowKey(!showKey)} edge="end" sx={{ color: "rgba(255,255,255,0.5)" }}>
                  {showKey ? <VisibilityOff /> : <Visibility />}
                </IconButton>
              </InputAdornment>
            )
          }}
        />

        <TextField
          label="Base URL"
          value={config.base_url || ""}
          onChange={(e) => setConfig({ ...config, base_url: e.target.value })}
          fullWidth
          variant="outlined"
          placeholder={config.provider === "ollama" ? "http://ollama:11434" : "https://api.openai.com/v1"}
          sx={{ "& .MuiOutlinedInput-root": { background: "rgba(0,0,0,0.2)" } }}
        />

        <Box sx={{ display: "flex", gap: 2 }}>
          <Button
            variant="contained"
            onClick={handleSave}
            disabled={saving}
            startIcon={<SaveIcon />}
            sx={{ background: "linear-gradient(135deg, #7c4dff, #00e5ff)" }}
          >
            {saving ? "Saving..." : "Save"}
          </Button>
          <Button
            variant="outlined"
            onClick={handleTest}
            disabled={testing}
            startIcon={<TestIcon />}
            sx={{ borderColor: "rgba(124,77,255,0.5)", color: "#7c4dff" }}
          >
            {testing ? "Testing..." : "Test Connection"}
          </Button>
        </Box>

        {testResult && (
          <Alert severity={testResult.success ? "success" : "error"} variant="filled">
            {testResult.success ? "Connection successful!" : testResult.error}
            {testResult.data && <pre className="code-block" style={{ marginTop: 8 }}>{JSON.stringify(testResult.data, null, 2)}</pre>}
          </Alert>
        )}
      </Box>
    </div>
  )
}
