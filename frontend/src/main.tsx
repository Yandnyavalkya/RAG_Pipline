import React from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import FeedbackCenter from './FeedbackCenter'
import './styles.css'
import './feedback-center.css'

createRoot(document.getElementById('root')!).render(<React.StrictMode><App /><FeedbackCenter /></React.StrictMode>)
