import React from "react"
import { Alert, Button, Box } from "@mui/material"

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }
  render() {
    if (this.state.hasError) {
      return (
        <Box sx={{ p: 4 }}>
          <Alert severity="error" variant="filled">Something went wrong: {this.state.error?.message}</Alert>
          <Button sx={{ mt: 2 }} variant="outlined" onClick={() => this.setState({ hasError: false })}>Try Again</Button>
        </Box>
      )
    }
    return this.props.children
  }
}
