import React, { useState, useEffect } from "react"
import { Box, Typography, Paper, Chip } from "@mui/material"
import { Wifi as WifiIcon, WifiOff as WifiOffIcon } from "@mui/icons-material"
import client from "../api/client"

export default function ConnectionStatus() {
  const [status, setStatus] = useState(null)

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await client.get("/whatsapp/status")
        setStatus(res.data)
      } catch { setStatus({ connected: false, error: "Cannot reach API" }) }
    }
    fetch()
    const interval = setInterval(fetch, 10000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="page-card">
      <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 3 }}>
        {status?.connected ? (
          <WifiIcon sx={{ color: "#00e676", fontSize: 40 }} />
        ) : (
          <WifiOffIcon sx={{ color: "#ff1744", fontSize: 40 }} />
        )}
        <Typography variant="h5" sx={{ fontWeight: 600 }}>
          WAHA Connection Status
        </Typography>
        <Chip
          label={status?.connected ? "Connected" : "Disconnected"}
          color={status?.connected ? "success" : "error"}
          variant="outlined"
        />
      </Box>
      <Paper sx={{ p: 3, background: "rgba(0,0,0,0.2)" }}>
        <pre className="code-block">{JSON.stringify(status, null, 2)}</pre>
      </Paper>
    </div>
  )
}
