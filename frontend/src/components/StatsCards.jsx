import React from "react"
import { Card, CardContent, Typography, Box } from "@mui/material"
import {
  Message as MessageIcon,
  Block as BlockIcon,
  SmartToy as AIIcon,
  VerifiedUser as ShieldIcon,
  People as PeopleIcon,
  Timer as TimerIcon
} from "@mui/icons-material"
import { useApp } from "../App"

const defaultStats = {
  messages_today: 0, blocked: 0, ai_replies: 0, approval_queue: 0,
  active_conversations: 0, uptime_hours: 0
}

export default function StatsCards() {
  const { stats } = useApp()
  const s = stats || defaultStats

  const cards = [
    { label: "Messages Today", value: s.messages_today, icon: <MessageIcon />, color: "#40c4ff" },
    { label: "Blocked", value: s.blocked, icon: <BlockIcon />, color: "#ff1744" },
    { label: "AI Replies", value: s.ai_replies, icon: <AIIcon />, color: "#7c4dff" },
    { label: "Approval Queue", value: s.approval_queue, icon: <ShieldIcon />, color: "#ff9100" },
    { label: "Active Chats", value: s.active_conversations, icon: <PeopleIcon />, color: "#00e676" },
    { label: "Uptime (hrs)", value: s.uptime_hours, icon: <TimerIcon />, color: "#e040fb" },
  ]

  return (
    <div className="stats-grid">
      {cards.map((card, i) => (
        <Card key={i} sx={{
          background: "linear-gradient(135deg, #1a1a3e 0%, #12122a 100%)",
          border: "1px solid rgba(124, 77, 255, 0.2)",
          borderRadius: 3,
          transition: "all 0.3s",
          "&:hover": {
            borderColor: "rgba(124, 77, 255, 0.5)",
            boxShadow: "0 4px 20px rgba(124, 77, 255, 0.15)",
            transform: "translateY(-2px)"
          }
        }}>
          <CardContent sx={{ display: "flex", alignItems: "center", gap: 2, p: 3 }}>
            <Box sx={{ color: card.color, opacity: 0.8 }}>{card.icon}</Box>
            <Box>
              <Typography variant="h4" sx={{ fontWeight: 700, color: "#fff" }}>{card.value}</Typography>
              <Typography variant="body2" sx={{ color: "rgba(255,255,255,0.5)" }}>{card.label}</Typography>
            </Box>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
