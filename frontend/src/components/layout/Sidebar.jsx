import { BookOpen, ClipboardCheck, FolderOpen, LayoutDashboard, LogOut, PlusCircle } from 'lucide-react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

function initials(name = '') {
  return name.split(' ').filter(Boolean).slice(0, 2).map((item) => item[0]).join('').toUpperCase();
}

export default function Sidebar() {
  const { user, logout } = useAuth();
  const linkBase = 'flex items-center gap-3 border-l-4 px-4 py-3 text-sm font-semibold transition';
  const linkClass = ({ isActive }) => isActive
    ? `${linkBase} border-teal bg-teal text-navy`
    : `${linkBase} border-transparent text-[#7a90b8] hover:bg-white/10 hover:text-white`;

  return (
    <aside className="flex min-h-screen w-full flex-col bg-navy text-white lg:w-60">
      <div className="px-5 py-6">
        <div className="font-mono text-xl font-semibold tracking-normal">ReqFlow <span className="text-teal">AI</span></div>
        <p className="mt-1 text-xs uppercase tracking-[0.12em] text-[#7a90b8]">TCS AI Fridays</p>
      </div>
      <nav className="flex-1 space-y-1">
        <NavLink to="/dashboard" className={linkClass}><LayoutDashboard size={18} />Dashboard</NavLink>
        {user?.role === 'analista' && <NavLink to="/requirements/new" className={linkClass}><PlusCircle size={18} />Nuevo Requisito</NavLink>}
        {user?.role === 'revisor' && <NavLink to="/dashboard?status=en_revision" className={linkClass}><ClipboardCheck size={18} />Pendientes</NavLink>}
        {user?.role === 'revisor' && <NavLink to="/projects" className={linkClass}><FolderOpen size={18} />Proyectos</NavLink>}
        <div className="mx-5 my-4 border-t border-white/10" />
        <a className={`${linkBase} border-transparent text-[#7a90b8] hover:bg-white/10 hover:text-white`} href="/docs/MANUAL_USUARIO.html" target="_blank" rel="noreferrer">
          <BookOpen size={18} />Documentacion
        </a>
      </nav>
      <div className="border-t border-white/10 p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue font-mono font-semibold text-teal">{initials(user?.full_name)}</div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-semibold">{user?.full_name}</p>
            <p className="text-xs font-semibold uppercase text-teal">{user?.role}</p>
          </div>
          <button className="rounded p-2 text-[#7a90b8] hover:bg-white/10 hover:text-white" onClick={logout} aria-label="Cerrar sesion" title="Cerrar sesion">
            <LogOut size={18} />
          </button>
        </div>
      </div>
    </aside>
  );
}
