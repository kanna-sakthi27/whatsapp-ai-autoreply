import React from "react"
import { NavLink } from "react-router-dom"
import {
  Dashboard as DashboardIcon,
  Message as MessageIcon,
  Send as SendIcon,
  VerifiedUser as ShieldIcon,
  SmartToy as AIIcon,
  Security as GuardIcon,
  Settings as SettingsIcon,
  ListAlt as LogsIcon,
  Wifi as StatusIcon
} from "@mui/icons-material"

const navItems = [
  { path: "/", label: "Dashboard", icon: <DashboardIcon /> },
  { path: "/messages", label: "Messages", icon: <MessageIcon /> },
  { path: "/send", label: "Send Message", icon: <SendIcon /> },
  { path: "/approval", label: "Approval Queue", icon: <ShieldIcon /> },
  { path: "/settings/ai", label: "AI Provider", icon: <AIIcon /> },
  { path: "/settings/guardrails", label: "Guard Rails", icon: <GuardIcon /> },
  { path: "/settings/general", label: "Settings", icon: <SettingsIcon /> },
  { path: "/logs", label: "Logs", icon: <LogsIcon /> },
  { path: "/status", label: "Connection", icon: <StatusIcon /> }
]

export default function Sidebar() {
  return (
    <nav className="sidebar">
      <div className="sidebar-logo">
        <h2>WA AI Guard</h2>
        <small>WhatsApp Auto-Reply</small>
      </div>
      {navItems.map((item) => (
        <NavLink
          key={item.path}
          to={item.path}
          className={({ isActive }) => "nav-item" + (isActive ? " active" : "")}
          end={item.path === "/"}
        >
          {item.icon}
          {item.label}
        </NavLink>
      ))}
      <div style={{ marginTop: "auto", padding: "20px", fontSize: "0.75rem", color: "rgba(255,255,255,0.2)", textAlign: "center" }}>
        v2.0.0
      </div>
    </nav>
  )
}
