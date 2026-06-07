import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Navbar.css';

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/giris');
  };

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-logo">
          🎓 EduAI <span>Platformu</span>
        </Link>
        <div className="navbar-menu">
          <Link to="/" className="nav-item">Ana Sayfa</Link>
          {user ? (
            <>
              <Link to="/profil" className="nav-item">Profilim</Link>
              <div className="user-profile-menu">
                <span className="navbar-username">Merhaba, {user.ad}</span>
                <button onClick={handleLogout} className="logout-btn">Çıkış Yap</button>
              </div>
            </>
          ) : (
            <div className="auth-buttons">
              <Link to="/giris" className="login-btn">Giriş Yap</Link>
              <Link to="/kayit" className="register-btn">Kayıt Ol</Link>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}
