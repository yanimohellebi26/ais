import { Navigate, Route, Routes } from 'react-router-dom'
import './App.css'
import RegisterPage from './pages/RegisterPage.jsx'

function App() {
  return (
    <div className="app-shell">
      <Routes>
        <Route path="/register" element={<RegisterPage />} />
        <Route path="*" element={<Navigate to="/register" replace />} />
      </Routes>
    </div>
  )
}

export default App
