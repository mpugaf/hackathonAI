import { ArrowLeft, ChevronDown, ChevronUp } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { getHistory, getRequirement } from '../api/requirements';
import LoadingOracle from '../components/ui/LoadingOracle';
import StatusBadge from '../components/ui/StatusBadge';
import { useToast } from '../context/AuthContext';

export default function HistoryPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [requirement, setRequirement] = useState(null);
  const [history, setHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [expanded, setExpanded] = useState({});

  useEffect(() => {
    Promise.all([getRequirement(id), getHistory(id)])
      .then(([detail, versions]) => {
        setRequirement(detail);
        setHistory(versions);
      })
      .catch((err) => showToast(err.message, 'error'))
      .finally(() => setIsLoading(false));
  }, [id, showToast]);

  if (isLoading) return <LoadingOracle isInline message="Cargando historial..." />;

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-silver bg-white p-4">
        <div>
          <button className="mb-3 inline-flex items-center gap-2 text-sm font-semibold text-blue" onClick={() => navigate(-1)}><ArrowLeft size={16} />Volver</button>
          <h2 className="text-lg font-semibold text-navy">{requirement?.title}</h2>
        </div>
        {requirement && <StatusBadge status={requirement.status} />}
      </header>
      <section className="space-y-0">
        {history.map((version, index) => {
          const isOpen = expanded[version.id];
          const aiReview = version.reviews?.find((review) => review.reviewer_type === 'ia');
          const humanReview = version.reviews?.find((review) => review.reviewer_type === 'humano');
          return (
            <div key={version.id} className="grid grid-cols-[56px_1fr]">
              <div className="flex flex-col items-center">
                <div className="flex h-11 w-11 items-center justify-center rounded-full bg-teal font-mono font-semibold text-navy">v{version.version_number}</div>
                {index < history.length - 1 && <div className="h-full w-px bg-silver" />}
              </div>
              <article className={`mb-4 rounded-lg border border-silver bg-white p-4 ${index === 0 ? 'border-l-4 border-l-teal' : ''}`}>
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <p className="text-sm font-semibold text-navy">{new Date(version.created_at).toLocaleString('es-CL')}</p>
                    <p className="font-mono text-xs text-teal">{version.model_used}</p>
                  </div>
                  {index === 0 && <span className="rounded bg-teal-lt px-2 py-1 text-xs font-semibold text-blue">Version actual</span>}
                </div>
                <p className="mt-3 text-sm text-slate">{isOpen ? version.generated_spec : `${version.generated_spec.slice(0, 200)}${version.generated_spec.length > 200 ? '...' : ''}`}</p>
                <div className="mt-3 flex flex-wrap items-center gap-2">
                  {aiReview && <span className="rounded bg-teal-lt px-2 py-1 font-mono text-xs text-blue">IA {aiReview.ai_score}</span>}
                  {humanReview && <span className="rounded bg-silver px-2 py-1 font-mono text-xs text-slate">{humanReview.decision}</span>}
                  <button className="inline-flex items-center gap-1 rounded-md border border-silver px-2 py-1 text-xs font-semibold text-blue" onClick={() => setExpanded((current) => ({ ...current, [version.id]: !isOpen }))}>
                    {isOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}Ver completa
                  </button>
                </div>
              </article>
            </div>
          );
        })}
        {!history.length && <div className="rounded-lg border border-silver bg-white p-8 text-center text-slate">Aun no hay versiones generadas.</div>}
      </section>
    </div>
  );
}
