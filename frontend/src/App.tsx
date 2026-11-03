import { BrowserRouter, Link, Route, Routes } from 'react-router-dom'
import MenuItemDetailsPage from './pages/MenuItemDetailsPage'
import MenuPage from './pages/MenuPage'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <header className="navbar">
        <Link to="/" className="brand">
          CampusEats
        </Link>
      </header>
      <main className="container">
        <Routes>
          <Route path="/" element={<MenuPage />} />
          <Route path="/menu/:menuItemId" element={<MenuItemDetailsPage />} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}

export default App