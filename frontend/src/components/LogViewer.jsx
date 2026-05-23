import React, { useState, useEffect, useCallback } from "react"
import {
  Box, Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, Chip, IconButton, Collapse, Typography, TextField, Select, MenuItem,
  FormControl, InputLabel, Button, InputAdornment
} from "@mui/material"
import {
  Search as SearchIcon, Delete as DeleteIcon, Refresh as RefreshIcon,
  ExpandMore, ExpandLess, FileDownload as ExportIcon, FilterList
} from "@mui/icons-material"
import client from "../api/client"
import { useApp } from "../App"

const LEVEL_COLORS = {
  DEBUG: "default", INFO: "info", WARNING: "warning",
  ERROR: "error", CRITICAL: "error"
}

export default function LogViewer() {
  const [logs, setLogs] = useState([])
  const [stats, setStats] = useState({ total: 0, errors: 0, warnings: 0, info: 0 })
  const [page, setPage] = useState(1)
  const [perPage, setPerPage] = useState(50)
  const [search, setSearch] = useState("")
  const [level, setLevel] = useState("")
  const [source, setSource] = useState("")
  const [expanded, setExpanded] = useState(null)
  const [totalItems, setTotalItems] = useState(0)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const { addToast } = useApp()

  const fetchLogs = useCallback(async () => {
    try {
      const params = new URLSearchParams()
      params.set("page", page)
      params.set("per_page", perPage)
      if (search) params.set("search", search)
      if (level) params.set("level", level)
      if (source) params.set("source", source)
      const res = await client.get("/logs?" + params.toString())
      const data = res.data
      if (data && data.items) {
        setLogs(data.items)
        setTotalItems(data.total || 0)
      } else if (Array.isArray(data)) {
        setLogs(data)
        setTotalItems(data.length)
      }
    } catch {}
  }, [page, perPage, search, level, source])

  const fetchStats = async () => {
    try {
      const res = await client.get("/logs/stats")
      if (res.data) setStats(res.data)
    } catch {}
  }

  useEffect(() => {
    fetchLogs()
    fetchStats()
  }, [fetchLogs])

  useEffect(() => {
    if (!autoRefresh) return
    const interval = setInterval(fetchLogs, 10000)
    return () => clearInterval(interval)
  }, [fetchLogs, autoRefresh])

  const handleClear = async () => {
    try {
      await client.delete("/api/logs")
      setLogs([])
      setTotalItems(0)
      addToast("Logs cleared", "success")
    } catch (err) {
      addToast("Failed to clear: " + err.message, "error")
    }
  }

  const totalPages = Math.ceil(totalItems / perPage) || 1

  return (
    <div className="page-card">
      <Box sx={{ display: "flex", gap: 2, mb: 2, flexWrap: "wrap", alignItems: "center" }}>
        <TextField
          size="small"
          placeholder="Search logs..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1) }}
          sx={{ minWidth: 250, "& .MuiOutlinedInput-root": { background: "rgba(0,0,0,0.2)" } }}
          InputProps={{
            startAdornment: <InputAdornment position="start"><SearchIcon sx={{ color: "rgba(255,255,255,0.3)" }} /></InputAdornment>
          }}
        />
        <FormControl size="small" sx={{ minWidth: 120, "& .MuiOutlinedInput-root": { background: "rgba(0,0,0,0.2)" } }}>
          <InputLabel>Level</InputLabel>
          <Select value={level} label="Level" onChange={(e) => { setLevel(e.target.value); setPage(1) }}>
            <MenuItem value="">All</MenuItem>
            <MenuItem value="DEBUG">DEBUG</MenuItem>
            <MenuItem value="INFO">INFO</MenuItem>
            <MenuItem value="WARNING">WARNING</MenuItem>
            <MenuItem value="ERROR">ERROR</MenuItem>
            <MenuItem value="CRITICAL">CRITICAL</MenuItem>
          </Select>
        </FormControl>
        <FormControl size="small" sx={{ minWidth: 120, "& .MuiOutlinedInput-root": { background: "rgba(0,0,0,0.2)" } }}>
          <InputLabel>Source</InputLabel>
          <Select value={source} label="Source" onChange={(e) => { setSource(e.target.value); setPage(1) }}>
            <MenuItem value="">All</MenuItem>
            <MenuItem value="system">System</MenuItem>
            <MenuItem value="ai">AI</MenuItem>
            <MenuItem value="whatsapp">WhatsApp</MenuItem>
            <MenuItem value="guard">Guard</MenuItem>
            <MenuItem value="api">API</MenuItem>
          </Select>
        </FormControl>
        <IconButton onClick={handleClear} sx={{ color: "#ff1744" }}><DeleteIcon /></IconButton>
        <IconButton onClick={() => setAutoRefresh(!autoRefresh)} sx={{ color: autoRefresh ? "#00e676" : "rgba(255,255,255,0.3)" }}><RefreshIcon /></IconButton>
      </Box>

      <Box sx={{ display: "flex", gap: 2, mb: 2 }}>
        <Chip label={"Total: " + stats.total} size="small" variant="outlined" sx={{ color: "rgba(255,255,255,0.6)" }} />
        <Chip label={"Errors: " + stats.errors} size="small" color="error" variant="outlined" />
        <Chip label={"Warnings: " + stats.warnings} size="small" color="warning" variant="outlined" />
      </Box>

      <TableContainer component={Paper} sx={{ background: "transparent" }}>
        <Table className="log-table">
          <TableHead>
            <TableRow>
              <TableCell>Time</TableCell>
              <TableCell>Level</TableCell>
              <TableCell>Source</TableCell>
              <TableCell>Message</TableCell>
              <TableCell></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {logs.map((log, i) => (
              <React.Fragment key={i}>
                <TableRow
                  onClick={() => setExpanded(expanded === i ? null : i)}
                  sx={{ cursor: "pointer", "&:hover": { background: "rgba(124,77,255,0.05)" } }}
                >
                  <TableCell sx={{ whiteSpace: "nowrap" }}>
                    {log.timestamp ? new Date(log.timestamp * 1000).toLocaleString() : "-"}
                  </TableCell>
                  <TableCell>
                    <Chip label={log.level || "INFO"} size="small" color={LEVEL_COLORS[log.level] || "default"} variant="outlined" />
                  </TableCell>
                  <TableCell>
                    <Chip label={log.source || "-"} size="small" variant="outlined" sx={{ color: "rgba(255,255,255,0.6)" }} />
                  </TableCell>
                  <TableCell sx={{ maxWidth: 400, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {log.message || ""}
                  </TableCell>
                  <TableCell>{expanded === i ? <ExpandLess /> : <ExpandMore />}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell colSpan={5} sx={{ p: 0 }}>
                    <Collapse in={expanded === i}>
                      <Box sx={{ p: 2, background: "rgba(0,0,0,0.2)" }}>
                        <pre className="code-block">{JSON.stringify(log, null, 2)}</pre>
                      </Box>
                    </Collapse>
                  </TableCell>
                </TableRow>
              </React.Fragment>
            ))}
            {logs.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} sx={{ textAlign: "center", color: "rgba(255,255,255,0.3)", py: 4 }}>
                  No logs found
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mt: 2 }}>
        <Typography variant="body2" sx={{ color: "rgba(255,255,255,0.5)" }}>
          Page {page} of {totalPages} ({totalItems} total)
        </Typography>
        <Box sx={{ display: "flex", gap: 1 }}>
          <Button size="small" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</Button>
          <Button size="small" disabled={page >= totalPages} onClick={() => setPage(page + 1)}>Next</Button>
        </Box>
      </Box>
    </div>
  )
}
