import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material'
import App from './App'
import './App.css'

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#7c4dff' },
    secondary: { main: '#00e5ff' },
    background: { default: '#0a0a1a', paper: '#12122a' },
    error: { main: '#ff1744' },
    warning: { main: '#ff9100' },
    success: { main: '#00e676' },
    info: { main: '#40c4ff' },
  },
  typography: {
    fontFamily: "'Inter', -apple-system, sans-serif",
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: { styleOverrides: { root: { textTransform: 'none' } } },
    MuiCard: { styleOverrides: { root: { backgroundImage: 'none' } } },
  },
})

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <App />
      </ThemeProvider>
    </BrowserRouter>
  </React.StrictMode>
)
