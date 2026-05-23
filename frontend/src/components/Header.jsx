import React from "react"
import { IconButton, Tooltip } from "@mui/material"
import { GitHub as GitHubIcon, Refresh as RefreshIcon } from "@mui/icons-material"
import { useApp } from "../App"

export default function Header({ title }) {
  const { addToast } = useApp()
  return (
    <div className="header">
      <h1>{title}</h1>
      <div className="header-actions">
        <Tooltip title="Refresh">
          <IconButton onClick={() => addToast("Refreshed", "info")} sx={{ color: "rgba(255,255,255,0.6)" }}>
            <RefreshIcon />
          </IconButton>
        </Tooltip>
        <Tooltip title="GitHub">
          <IconButton
            href="https://github.com/kanna-sakthi27/whatsapp-ai-autoreply"
            target="_blank"
            sx={{ color: "rgba(255,255,255,0.6)" }}
          >
            <GitHubIcon />
          </IconButton>
        </Tooltip>
      </div>
    </div>
  )
}
