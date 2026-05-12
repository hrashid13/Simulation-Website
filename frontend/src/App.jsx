import { BrowserRouter, Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import AmusementParkPage from './pages/AmusementParkPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/amusement-park" element={<AmusementParkPage />} />
      </Routes>
    </BrowserRouter>
  )
}
