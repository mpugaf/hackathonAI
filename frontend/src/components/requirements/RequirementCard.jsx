import { Clock, Eye, GitBranch } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import StatusBadge from '../ui/StatusBadge';

const border = {
  borrador: 'border-l-slate',
  en_revision: 'border-l-warn',
  aprobado: 'border-l-ok',
  rechazado: 'border-l-danger'
};

function relativeDate(date) {
  const diff = (new Date(date).getTime() - Date.now()) / 1000;
  const units = [
    ['year', 31536000],
    ['month', 2592000],
    ['day', 86400],
    ['hour', 3600],
    ['minute', 60]
  ];
  const formatter = new Intl.RelativeTimeFormat('es', { numeric: 'auto' });
  for (const [unit, seconds] of units) {
    if (Math.abs(diff) >= seconds) {
      return formatter.format(Math.round(diff / seconds), unit);
    }
  }
  return formatter.format(Math.round(diff), 'second');
}

export default function RequirementCard({ requirement }) {
  const navigate = useNavigate();
  const { user } = useAuth();
  const canReview = user?.role === 'revisor' && requirement.status === 'en_revision';

  return (
    <article className={`rounded-lg border border-silver border-l-4 bg-white p-5 transition duration-150 hover:-translate-y-px hover:shadow-md ${border[requirement.status] ?? border.borrador}`}>
      <div className="flex items-start justify-between gap-3">
        <h2 className="line-clamp-2 text-base font-semibold text-navy">{requirement.title}</h2>
        <StatusBadge status={requirement.status} size="sm" />
      </div>
      <div className="mt-4 flex flex-wrap items-center gap-4 text-sm text-slate">
        <span className="flex items-center gap-1.5"><Clock size={15} />{relativeDate(requirement.created_at)}</span>
        <span className="flex items-center gap-1.5 font-mono text-teal"><GitBranch size={15} />v{requirement.version_count}</span>
      </div>
      <div className="mt-5 flex flex-wrap gap-2">
        <button className="inline-flex items-center gap-2 rounded-md border border-silver px-3 py-2 text-sm font-semibold text-blue hover:bg-silver" onClick={() => navigate(`/requirements/${requirement.id}`)}>
          <Eye size={16} />Ver detalle
        </button>
        {canReview && (
          <button className="rounded-md bg-teal px-3 py-2 text-sm font-semibold text-navy hover:bg-[#17dcc8]" onClick={() => navigate(`/requirements/${requirement.id}/review`)}>
            Revisar
          </button>
        )}
      </div>
    </article>
  );
}
