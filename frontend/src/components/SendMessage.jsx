import React, { useState } from "react"
import { TextField, Button, Box, Select, MenuItem, FormControl, InputLabel, Alert } from "@mui/material"
import { Send as SendIcon } from "@mui/icons-material"
import client from "../api/client"
import { useApp } from "../App"

export default function SendMessage() {
  const [phone, setPhone] = useState("")
  const [message, setMessage] = useState("")
  const [sending, setSending] = useState(false)
  const [result, setResult] = useState(null)
  const { addToast } = useApp()

  const handleSend = async () => {
    if (!phone || !message) {
      addToast("Phone and message are required", "warning")
      return
    }
    setSending(true)
    setResult(null)
    try {
      const res = await client.post("/send", {
        phone: phone.replace(/[^0-9]/g, ""),
        message: message
      })
      setResult({ success: true, data: res.data })
      addToast("Message sent successfully", "success")
      setMessage("")
    } catch (err) {
      setResult({ success: false, error: err.message })
      addToast("Failed to send: " + err.message, "error")
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="page-card">
      <Box sx={{ display: "flex", flexDirection: "column", gap: 3, maxWidth: 600 }}>
        <TextField
          label="Phone Number"
          placeholder="+1234567890"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          fullWidth
          variant="outlined"
          sx={{ "& .MuiOutlinedInput-root": { background: "rgba(0,0,0,0.2)" } }}
        />
        <TextField
          label="Message"
          placeholder="Type your message..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          multiline
          rows={4}
          fullWidth
          variant="outlined"
          sx={{ "& .MuiOutlinedInput-root": { background: "rgba(0,0,0,0.2)" } }}
        />
        <Button
          variant="contained"
          onClick={handleSend}
          disabled={sending}
          startIcon={<SendIcon />}
          sx={{
            background: "linear-gradient(135deg, #7c4dff, #00e5ff)",
            "&:hover": { opacity: 0.9 },
            py: 1.5
          }}
        >
          {sending ? "Sending..." : "Send Message"}
        </Button>
        {result && (
          <Alert severity={result.success ? "success" : "error"} variant="filled">
            {result.success ? "Message sent!" : result.error}
          </Alert>
        )}
      </Box>
    </div>
  )
}
