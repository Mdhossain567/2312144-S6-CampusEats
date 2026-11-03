import { BrowserRouter, Link, Route, Routes } from 'react-router-dom'
import EditMenuItemPage from './pages/EditMenuItemPage'
import MenuItemDetailsPage from './pages/MenuItemDetailsPage'
import MenuPage from './pages/MenuPage'
import NewMenuItemPage from './pages/NewMenuItemPage'
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
          <Route path="/menu/new" element={<NewMenuItemPage />} />
          <Route path="/menu/:menuItemId" element={<MenuItemDetailsPage />} />
          <Route path="/menu/:menuItemId/edit" element={<EditMenuItemPage />} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}

export default App