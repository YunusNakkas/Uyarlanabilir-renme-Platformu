import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { PublicRoute, PrivateRoute } from './components/RouteGuard';
import Navbar from './components/Navbar';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ProfilePage from './pages/ProfilePage';
import ForgotPasswordPage from './pages/ForgotPasswordPage';

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="app-layout">
          <Navbar />
          <main className="main-content">
            <Routes>
              {/* Public rotalar */}
              <Route path="/giris"  element={<PublicRoute><LoginPage /></PublicRoute>} />
              <Route path="/kayit"  element={<PublicRoute><RegisterPage /></PublicRoute>} />
              <Route path="/sifremi-unuttum" element={<ForgotPasswordPage />} />

              {/* Private rotalar */}
              <Route path="/profil" element={<PrivateRoute><ProfilePage /></PrivateRoute>} />

              {/* Yönlendirme */}
              <Route path="/" element={<Navigate to="/giris" replace />} />
              <Route path="*" element={<Navigate to="/giris" replace />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
}
