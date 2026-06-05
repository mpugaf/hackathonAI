import { PlusCircle, RefreshCw, Search } from 'lucide-react';
import { useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import RequirementCard from '../components/requirements/RequirementCard';
import LoadingOracle from '../components/ui/LoadingOracle';
import { useAuth } from '../context/AuthContext';
import useRequirements from '../hooks/useRequirements';

export default function DashboardPage() {
  const { requirements, isLoading, error, refresh } = useRequirements();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [filters, setFilters] = useState({ status: searchParams.get('status') ?? 'todos', search: '' });

  const filtered = useMemo(() => requirements.filter((item) => {
    const statusOk = filters.status === 'todos' || item.status === filters.status;
    const searchOk = !filters.search || item.title.toLowerCase().includes(filters.search.toLowerCase());
    return statusOk && searchOk;
  }), [requirements, filters]);

  const metrics = {
    Total: requirements.length,
    Borradores: requirements.filter((item) => item.status === 'borrador').length,
    'En Revision': requirements.filter((item) => item.status === 'en_revision').length,
    Aprobados: requirements.filter((item) => item.status === 'aprobado').length
  };

  return (
    <div className="space-y-5">
      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Object.entries(metrics).map(([label, value]) => (
          <div key={label} className="rounded-lg border border-silver bg-white p-4">
            <p className="text-sm font-semibold text-slate">{label}</p>
            <p className="mt-2 font-mono text-3xl font-semibold text-blue">{value}</p>
          </div>
        ))}
      </section>
      <section className="flex flex-col gap-3 rounded-lg border border-silver bg-white p-4 lg:flex-row lg:items-center">
        <select className="rounded-md border border-silver px-3 py-2 text-sm outline-none focus:border-teal" value={filters.status} onChange={(e) => setFilters((current) => ({ ...current, status: e.target.value }))}>
          <option value="todos">Todos los estados</option>
          <option value="borrador">Borrador</option>
          <option value="en_revision">En Revision</option>
          <option value="aprobado">Aprobado</option>
          <option value="rechazado">Rechazado</option>
        </select>
        <div className="relative flex-1">
          <Search className="absolute left-3 top-2.5 text-slate" size={18} />
          <input className="w-full rounded-md border border-silver py-2 pl-10 pr-3 text-sm outline-none focus:border-teal" placeholder="Buscar por titulo" value={filters.search} onChange={(e) => setFilters((current) => ({ ...current, search: e.target.value }))} />
        </div>
        <button className="inline-flex items-center justify-center gap-2 rounded-md border border-silver px-4 py-2 text-sm font-semibold text-blue hover:bg-silver" onClick={refresh}>
          <RefreshCw size={16} className={isLoading ? 'animate-spin' : ''} />Actualizar
        </button>
      </section>
      {error && <p className="rounded-md bg-red-50 p-3 text-sm font-medium text-danger">{error}</p>}
      {isLoading ? <LoadingOracle isInline /> : filtered.length ? (
        <section className="grid gap-4 lg:grid-cols-2">
          {filtered.map((requirement) => <RequirementCard key={requirement.id} requirement={requirement} />)}
        </section>
      ) : (
        <section className="rounded-lg border border-silver bg-white p-10 text-center">
          <svg className="mx-auto h-28 w-28" viewBox="0 0 120 120" role="img" aria-label="Sin requisitos">
            <rect x="24" y="18" width="72" height="84" rx="8" fill="#e8edf4" />
            <path d="M38 42h44M38 58h34M38 74h26" stroke="#1a3a6b" strokeWidth="5" strokeLinecap="round" />
            <circle cx="88" cy="88" r="14" fill="#00c9b1" />
          </svg>
          <h2 className="mt-4 text-lg font-semibold text-navy">No hay requisitos aun</h2>
          {user?.role === 'analista' && <button className="mt-4 rounded-md bg-blue px-4 py-2 text-sm font-semibold text-white" onClick={() => navigate('/requirements/new')}>Crear el primero</button>}
        </section>
      )}
      {user?.role === 'analista' && (
        <button className="fixed bottom-6 right-6 inline-flex items-center gap-2 rounded-full bg-teal px-5 py-3 font-semibold text-navy shadow-lg" onClick={() => navigate('/requirements/new')}>
          <PlusCircle size={18} />Nuevo Requisito
        </button>
      )}
    </div>
  );
}
