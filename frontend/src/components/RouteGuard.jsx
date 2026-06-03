import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

/** Sadece giriş yapılmamış kullanıcılara açık rota */
export function PublicRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="flex-center" style={{ minHeight: '100vh' }}><div className="spinner" /></div>;
  return user ? <Navigate to="/profil" replace /> : children;
}

/** Sadece giriş yapmış kullanıcılara açık rota */
export function PrivateRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="flex-center" style={{ minHeight: '100vh' }}><div className="spinner" /></div>;
  return user ? children : <Navigate to="/giris" replace />;
}
