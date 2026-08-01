import { BrowserRouter, Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import AmusementParkPage from './pages/AmusementParkPage'
import HospitalPage from './pages/HospitalPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/amusement-park" element={<AmusementParkPage />} />
        <Route path="/hospital" element={<HospitalPage />} />
      </Routes>
    </BrowserRouter>
  )
}
