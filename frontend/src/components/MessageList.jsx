import React, { useState, useEffect } from "react"
import {
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, Typography, Chip, IconButton, Collapse, Box, TextField, InputAdornment
} from "@mui/material"
import { Search as SearchIcon, Delete as DeleteIcon, ExpandMore, ExpandLess } from "@mui/icons-material"
import client from "../api/client"
import { useApp } from "../App"

export default function MessageList() {
  const [messages, setMessages] = useState([])
  const [search, setSearch] = useState("")
  const [expanded, setExpanded] = useState(null)
  const { addToast } = useApp()

  useEffect(() => {
    const fetchMessages = async () => {
      try {
        const res = await client.get("/messages")
        setMessages(Array.isArray(res.data) ? res.data : [])
      } catch (err) {
        console.error("Message fetch error:", err)
      }
    }
    fetchMessages()
    const interval = setInterval(fetchMessages, 15000)
    return () => clearInterval(interval)
  }, [])

  const handleClear = async () => {
    try {
      await client.delete("/messages")
      setMessages([])
      addToast("Message history cleared", "success")
    } catch (err) {
      addToast("Failed to clear messages: " + err.message, "error")
    }
  }

  const filtered = messages.filter(m => {
    if (!search) return true
    const q = search.toLowerCase()
    return (m.message || "").toLowerCase().includes(q) ||
           (m.phone || "").toLowerCase().includes(q) ||
           (m.status || "").toLowerCase().includes(q)
  })

  const getStatusColor = (status) => {
    switch(status) {
      case "sent": return "success"
      case "received": return "info"
      case "blocked": return "error"
      case "pending": return "warning"
      case "failed": return "error"
      default: return "default"
    }
  }

  return (
    <div className="page-card">
      <Box sx={{ display: "flex", justifyContent: "space-between", mb: 2, gap: 2 }}>
        <TextField
          size="small"
          placeholder="Search messages..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          sx={{ minWidth: 300, "& .MuiOutlinedInput-root": { background: "rgba(0,0,0,0.2)" } }}
          InputProps={{
            startAdornment: <InputAdornment position="start"><SearchIcon sx={{ color: "rgba(255,255,255,0.3)" }} /></InputAdornment>
          }}
        />
        <IconButton onClick={handleClear} sx={{ color: "#ff1744" }}>
          <DeleteIcon />
        </IconButton>
      </Box>

      <TableContainer component={Paper} sx={{ background: "transparent" }}>
        <Table className="log-table">
          <TableHead>
            <TableRow>
              <TableCell>Phone</TableCell>
              <TableCell>Message</TableCell>
              <TableCell>Direction</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Time</TableCell>
              <TableCell></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filtered.map((msg, i) => (
              <React.Fragment key={i}>
                <TableRow
                  onClick={() => setExpanded(expanded === i ? null : i)}
                  sx={{ cursor: "pointer", "&:hover": { background: "rgba(124,77,255,0.05)" } }}
                >
                  <TableCell>{msg.phone || "-"}</TableCell>
                  <TableCell sx={{ maxWidth: 300, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {msg.message?.substring(0, 80) || "-"}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={msg.direction || "-"}
                      size="small"
                      variant="outlined"
                      color={msg.direction === "incoming" ? "info" : "primary"}
                    />
                  </TableCell>
                  <TableCell>
                    <Chip label={msg.status || "-"} size="small" color={getStatusColor(msg.status)} />
                  </TableCell>
                  <TableCell>{msg.timestamp ? new Date(msg.timestamp * 1000).toLocaleString() : "-"}</TableCell>
                  <TableCell>{expanded === i ? <ExpandLess /> : <ExpandMore />}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell colSpan={6} sx={{ p: 0 }}>
                    <Collapse in={expanded === i}>
                      <Box sx={{ p: 2, background: "rgba(0,0,0,0.2)" }}>
                        <pre className="code-block">{JSON.stringify(msg, null, 2)}</pre>
                      </Box>
                    </Collapse>
                  </TableCell>
                </TableRow>
              </React.Fragment>
            ))}
            {filtered.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} sx={{ textAlign: "center", color: "rgba(255,255,255,0.3)", py: 4 }}>
                  No messages found
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </div>
  )
}
