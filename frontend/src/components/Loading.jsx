import React from "react"
import { CircularProgress, Box, Typography } from "@mui/material"

export default function Loading({ message = "Loading..." }) {
  return (
    <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", py: 8, gap: 2 }}>
      <CircularProgress sx={{ color: "#7c4dff" }} />
      <Typography variant="body2" sx={{ color: "rgba(255,255,255,0.5)" }}>{message}</Typography>
    </Box>
  )
}
