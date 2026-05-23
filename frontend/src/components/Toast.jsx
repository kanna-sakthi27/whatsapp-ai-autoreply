import React from "react"
import { Alert, Snackbar } from "@mui/material"
import { useApp } from "../App"

export default function Toast() {
  const { toasts } = useApp()
  return (
    <div className="toast-container">
      {toasts.map((t) => (
        <Snackbar key={t.id} open={true} autoHideDuration={4000} anchorOrigin={{ vertical: "top", horizontal: "right" }}>
          <Alert severity={t.severity} variant="filled" sx={{ minWidth: 300 }}>
            {t.message}
          </Alert>
        </Snackbar>
      ))}
    </div>
  )
}
