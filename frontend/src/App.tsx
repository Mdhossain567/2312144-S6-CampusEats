import { BrowserRouter, Link, Route, Routes } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute'
import { AuthProvider, useAuth } from './context/AuthContext'
import { CartProvider, useCart } from './context/CartContext'
import EditMenuItemPage from './pages/EditMenuItemPage'
import LoginPage from './pages/LoginPage'
import MenuItemDetailsPage from './pages/MenuItemDetailsPage'
import MenuPage from './pages/MenuPage'
import MyOrdersPage from './pages/MyOrdersPage'
import NewMenuItemPage from './pages/NewMenuItemPage'
import ProfilePage from './pages/ProfilePage'
import RegisterPage from './pages/RegisterPage'
import './App.css'

function NavBar() {
  const { user, logout } = useAuth()
  const { clear, count } = useCart()

  function handleLogout() {
    logout()
    clear()
  }

  return (
    <header className="navbar">
      <Link to="/" className="brand">
        CampusEats
      </Link>
      <nav className="nav-right">
        {user ? (
          <>
            {user.role === 'customer' && (
              <Link to="/orders" className="nav-link">
                My orders{count > 0 ? ` (cart: ${count})` : ''}
              </Link>
            )}
            <Link to="/profile" className="nav-link">
              {user.name} ({user.role})
            </Link>
            <button className="nav-button" onClick={handleLogout}>
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
        <CartProvider>
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
              <Route
                path="/orders"
                element={
                  <ProtectedRoute roles={['customer']}>
                    <MyOrdersPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/menu/new"
                element={
                  <ProtectedRoute roles={['admin']}>
                    <NewMenuItemPage />
                  </ProtectedRoute>
                }
              />
              <Route path="/menu/:menuItemId" element={<MenuItemDetailsPage />} />
              <Route
                path="/menu/:menuItemId/edit"
                element={
                  <ProtectedRoute roles={['admin']}>
                    <EditMenuItemPage />
                  </ProtectedRoute>
                }
              />
            </Routes>
          </main>
        </CartProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App