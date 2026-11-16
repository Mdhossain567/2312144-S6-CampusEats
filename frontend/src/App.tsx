import { BrowserRouter, Link, Route, Routes } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute'
import { AuthProvider, useAuth } from './context/AuthContext'
import EditMenuItemPage from './pages/EditMenuItemPage'
import LoginPage from './pages/LoginPage'
import MenuItemDetailsPage from './pages/MenuItemDetailsPage'
import MenuPage from './pages/MenuPage'
import NewMenuItemPage from './pages/NewMenuItemPage'
import ProfilePage from './pages/ProfilePage'
import RegisterPage from './pages/RegisterPage'
import './App.css'

function NavBar() {
  const { user, logout } = useAuth()

  return (
    <header className="navbar">
      <Link to="/" className="brand">
        CampusEats
      </Link>
      <nav className="nav-right">
        {user ? (
          <>
            <Link to="/profile" className="nav-link">
              {user.name} ({user.role})
            </Link>
            <button className="nav-button" onClick={logout}>
              Log out
            </button>
          </>
        ) : (
          <>
            <Link to="/login" className="nav-link">
              Log in
            </Link>
            <Link to="/register" className="nav-link">
              Sign up
            </Link>
          </>
        )}
      </nav>
    </header>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <NavBar />
        <main className="container">
          <Routes>
            <Route path="/" element={<MenuPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <ProfilePage />
                </ProtectedRoute>
              }
            />
            <Route path="/menu/new" element={<NewMenuItemPage />} />
            <Route path="/menu/:menuItemId" element={<MenuItemDetailsPage />} />
            <Route path="/menu/:menuItemId/edit" element={<EditMenuItemPage />} />
          </Routes>
        </main>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App