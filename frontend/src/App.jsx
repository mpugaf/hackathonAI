import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import AppLayout from './components/layout/AppLayout';
import LoadingOracle from './components/ui/LoadingOracle';
import { useAuth } from './context/AuthContext';
import DashboardPage from './pages/DashboardPage';
import HistoryPage from './pages/HistoryPage';
import LoginPage from './pages/LoginPage';
import NewRequirementPage from './pages/NewRequirementPage';
import RequirementDetailPage from './pages/RequirementDetailPage';
import ReviewPage from './pages/ReviewPage';

function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();
  if (isLoading) return <div className="p-8"><LoadingOracle isInline message="Cargando sesion..." /></div>;
  if (!isAuthenticated) return <Navigate to="/login" replace state={{ from: location }} />;
  return children;
}

function RoleRoute({ roles, children }) {
  const { user, showToast } = useAuth();
  if (!roles.includes(user?.role)) {
    showToast('No tienes permisos para acceder a esta pantalla', 'warn');
    return <Navigate to="/dashboard" replace />;
  }
  return children;
}

function NotFound() {
  return (
    <div className="rounded-lg border border-silver bg-white p-8 text-center">
      <h1 className="text-xl font-semibold text-navy">Pagina no encontrada</h1>
      <a className="mt-4 inline-block rounded-md bg-blue px-4 py-2 text-sm font-semibold text-white" href="/dashboard">Volver</a>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/requirements/new" element={<RoleRoute roles={['analista']}><NewRequirementPage /></RoleRoute>} />
        <Route path="/requirements/:id" element={<RequirementDetailPage />} />
        <Route path="/requirements/:id/review" element={<RoleRoute roles={['revisor']}><ReviewPage /></RoleRoute>} />
        <Route path="/requirements/:id/history" element={<HistoryPage />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
