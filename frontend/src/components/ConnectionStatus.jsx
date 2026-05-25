import React, { useState, useEffect } from "react"
import { Box, Typography, Paper, Chip, Alert } from "@mui/material"
import { Wifi as WifiIcon, WifiOff as WifiOffIcon } from "@mui/icons-material"
import client from "../api/client"

export default function ConnectionStatus() {
const [status, setStatus] = useState(null)
const [fetchError, setFetchError] = useState(null)

const fetchStatus = async () => {
try {
const res = await client.get("/whatsapp/status")
setStatus(res.data)
setFetchError(null)
} catch (err) {
setStatus({ connected: false, error: err.message })
setFetchError(`API call failed: ${err.message}`)
}
}

useEffect(() => {
fetchStatus()
const interval = setInterval(fetchStatus, 10000)
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

{fetchError && (
<Alert severity="warning" sx={{ mb: 2 }}>
{fetchError}. Check that all containers are running:
<code style={{ display: 'block', marginTop: 8 }}>docker compose ps</code>
<code style={{ display: 'block' }}>docker compose logs ai-service</code>
</Alert>
)}

<Paper sx={{ p: 3, background: "rgba(0,0,0,0.2)" }}>
<pre className="code-block">{JSON.stringify(status, null, 2)}</pre>
</Paper>
</div>
)
}
