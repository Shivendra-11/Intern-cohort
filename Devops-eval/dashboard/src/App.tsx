// src/App.tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import DashboardPage from './pages/DashboardPage'
import DetailPage from './pages/DetailPage'
import ServicesHubPage from './pages/ServicesHubPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/hub" element={<ServicesHubPage />} />
        <Route path="/task/:taskId" element={<DetailPage />} />
        <Route path="*" element={<DashboardPage />} />
      </Routes>
    </BrowserRouter>
  )
}
