import React, { useState, useEffect } from "react"
import {
  Box, Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Button, Chip, Typography, Paper, Collapse
} from "@mui/material"
import { CheckCircle as ApproveIcon, Cancel as RejectIcon, ExpandMore, ExpandLess } from "@mui/icons-material"
import client from "../api/client"
import { useApp } from "../App"

export default function ApprovalQueue() {
  const [queue, setQueue] = useState([])
  const [expanded, setExpanded] = useState(null)
  const [processing, setProcessing] = useState({})
  const { addToast } = useApp()

  const fetchQueue = async () => {
    try {
      const res = await client.get("/guard-queue")
      setQueue(Array.isArray(res.data) ? res.data : [])
    } catch { setQueue([]) }
  }

  useEffect(() => {
    fetchQueue()
    const interval = setInterval(fetchQueue, 5000)
    return () => clearInterval(interval)
  }, [])

  const handleApprove = async (idx) => {
    setProcessing(prev => ({ ...prev, [idx]: true }))
    try {
      await client.post("/guard-queue/approve", { index: idx })
      addToast("Message approved and sent", "success")
      fetchQueue()
    } catch (err) {
      addToast("Approval failed: " + err.message, "error")
    } finally {
      setProcessing(prev => ({ ...prev, [idx]: false }))
    }
  }

  const handleReject = async (idx) => {
    try {
      await client.delete("/guard-queue/" + idx)
      addToast("Message rejected", "info")
      fetchQueue()
    } catch (err) {
      addToast("Failed to reject: " + err.message, "error")
    }
  }

  return (
    <div className="page-card">
      <Box sx={{ display: "flex", justifyContent: "space-between", mb: 2 }}>
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          Queue ({queue.length})
        </Typography>
      </Box>
      {queue.length === 0 ? (
        <Typography sx={{ color: "rgba(255,255,255,0.3)", textAlign: "center", py: 4 }}>
          No messages pending approval
        </Typography>
      ) : (
        <TableContainer component={Paper} sx={{ background: "transparent" }}>
          <Table className="log-table">
            <TableHead>
              <TableRow>
                <TableCell>Chat ID</TableCell>
                <TableCell>Reply Preview</TableCell>
                <TableCell>Time</TableCell>
                <TableCell>Actions</TableCell>
                <TableCell></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {queue.map((item, idx) => (
                <React.Fragment key={idx}>
                  <TableRow onClick={() => setExpanded(expanded === idx ? null : idx)} sx={{ cursor: "pointer" }}>
                    <TableCell>{item.chat_id || item.phone || "-"}</TableCell>
                    <TableCell sx={{ maxWidth: 300, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {(item.reply || item.message || "").substring(0, 80)}
                    </TableCell>
                    <TableCell>{item.timestamp ? new Date(item.timestamp * 1000).toLocaleString() : "-"}</TableCell>
                    <TableCell>
                      <Button
                        size="small"
                        variant="contained"
                        color="success"
                        onClick={(e) => { e.stopPropagation(); handleApprove(idx); }}
                        disabled={processing[idx]}
                        sx={{ mr: 1, minWidth: 80 }}
                        startIcon={<ApproveIcon />}
                      >
                        {processing[idx] ? "..." : "Send"}
                      </Button>
                      <Button
                        size="small"
                        variant="outlined"
                        color="error"
                        onClick={(e) => { e.stopPropagation(); handleReject(idx); }}
                        startIcon={<RejectIcon />}
                      >
                        Reject
                      </Button>
                    </TableCell>
                    <TableCell>{expanded === idx ? <ExpandLess /> : <ExpandMore />}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell colSpan={5} sx={{ p: 0 }}>
                      <Collapse in={expanded === idx}>
                        <Box sx={{ p: 2, background: "rgba(0,0,0,0.2)" }}>
                          <pre className="code-block">{JSON.stringify(item, null, 2)}</pre>
                        </Box>
                      </Collapse>
                    </TableCell>
                  </TableRow>
                </React.Fragment>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </div>
  )
}
