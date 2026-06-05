import { Bot, Clock, History, MessageSquareWarning, Send, Sparkles } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { generateRequirement, reviewAI, updateRequirement } from '../api/requirements';
import AIFeedbackPanel from '../components/requirements/AIFeedbackPanel';
import ExportButton from '../components/requirements/ExportButton';
import SpecEditor from '../components/requirements/SpecEditor';
import LoadingOracle from '../components/ui/LoadingOracle';
import StatusBadge from '../components/ui/StatusBadge';
import { useAuth, useToast } from '../context/AuthContext';
import useRequirementDetail from '../hooks/useRequirementDetail';

export default function RequirementDetailPage() {
  const { id } = useParams();
  const { user } = useAuth();
  const { showToast } = useToast();
  const { requirement, setRequirement, isLoading, error, refresh } = useRequirementDetail(id);
  const [editedSpec, setEditedSpec] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isReviewing, setIsReviewing] = useState(false);
  const [title, setTitle] = useState('');

  useEffect(() => {
    setEditedSpec(requirement?.latest_version?.generated_spec ?? '');
    setTitle(requirement?.title ?? '');
  }, [requirement]);

  const canEdit = user?.role === 'analista' && requirement?.status === 'borrador';

  const saveTitle = async () => {
    if (!canEdit || title === requirement.title) return;
    try {
      const updated = await updateRequirement(id, { title });
      setRequirement((current) => ({ ...current, title: updated.title }));
      showToast('Titulo actualizado', 'success');
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const generate = async () => {
    setIsGenerating(true);
    try {
      await generateRequirement(id);
      showToast('Especificacion generada', 'success');
      await refresh();
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setIsGenerating(false);
    }
  };

  const sendReview = async () => {
    setIsReviewing(true);
    try {
      await reviewAI(id);
      showToast('Requisito enviado a revision', 'success');
      await refresh();
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setIsReviewing(false);
    }
  };

  if (isLoading) return <LoadingOracle isInline message="Cargando requisito..." />;
  if (error) return <p className="rounded-md bg-red-50 p-3 text-sm text-danger">{error}</p>;
  if (!requirement) return null;

  return (
    <div className="relative grid gap-5 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.35fr)]">
      {(isGenerating || isReviewing) && <LoadingOracle message={isGenerating ? 'Generando especificacion...' : 'El Revisor IA esta evaluando...'} />}
      <section className="space-y-4">
        <div className="rounded-lg border border-silver bg-white p-5">
          <div className="flex items-start justify-between gap-3">
            {canEdit ? (
              <input className="w-full rounded-md border border-silver px-3 py-2 text-lg font-semibold text-navy outline-none focus:border-teal" value={title} onChange={(e) => setTitle(e.target.value)} onBlur={saveTitle} />
            ) : (
              <h2 className="text-lg font-semibold text-navy">{requirement.title}</h2>
            )}
            <StatusBadge status={requirement.status} />
          </div>
          <label className="mt-5 block text-sm font-semibold text-navy">
            Requisito original
            <textarea className="mt-2 min-h-40 w-full rounded-md border border-silver bg-[#f8fafc] p-3 font-mono text-sm text-slate" value={requirement.raw_input} readOnly />
          </label>
          <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
            <div><dt className="font-semibold text-slate">Version actual</dt><dd className="font-mono text-teal">v{requirement.latest_version?.version_number ?? 0}</dd></div>
            <div><dt className="font-semibold text-slate">Modelo usado</dt><dd className="font-mono text-blue">{requirement.latest_version?.model_used ?? 'Pendiente'}</dd></div>
            <div><dt className="font-semibold text-slate">Fecha</dt><dd>{new Date(requirement.created_at).toLocaleString('es-CL')}</dd></div>
            <div><dt className="font-semibold text-slate">Proyecto</dt><dd className="font-mono text-slate">{requirement.project_id.slice(0, 8)}</dd></div>
          </dl>
          <div className="mt-5 flex flex-wrap gap-2">
            {canEdit && (
              <>
                <button className="inline-flex items-center gap-2 rounded-md bg-blue px-4 py-2 text-sm font-semibold text-white hover:bg-navy" onClick={generate}><Sparkles size={16} />Generar con IA</button>
                <button className="inline-flex items-center gap-2 rounded-md border border-teal px-4 py-2 text-sm font-semibold text-blue hover:bg-teal-lt disabled:opacity-50" onClick={sendReview} disabled={!requirement.latest_version}><Send size={16} />Enviar a Revision</button>
              </>
            )}
            {requirement.status === 'aprobado' && <ExportButton requirementId={id} />}
            <Link className="inline-flex items-center gap-2 rounded-md border border-silver px-4 py-2 text-sm font-semibold text-slate hover:bg-silver" to={`/requirements/${id}/history`}><History size={16} />Historial</Link>
          </div>
        </div>
        {requirement.status === 'rechazado' && requirement.latest_human_review && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-5">
            <div className="mb-3 flex items-center gap-2 text-sm font-bold text-danger">
              <MessageSquareWarning size={18} />
              El revisor ha devuelto el requisito con los siguientes alcances:
            </div>
            <ul className="space-y-1.5 pl-1">
              {requirement.latest_human_review.feedback
                .split(/\n+/)
                .map((line) => line.trim())
                .filter(Boolean)
                .map((line, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-danger">
                    <span className="mt-0.5 shrink-0 text-red-400">•</span>
                    <span>{line.replace(/^[-•*]\s*/, '')}</span>
                  </li>
                ))}
            </ul>
            <p className="mt-3 text-xs text-red-400">
              Revisa cada punto y vuelve a generar la especificación con "Generar con IA".
            </p>
          </div>
        )}
        {requirement.status === 'aprobado' && (
          <div className="flex items-start gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-[#065f46]"><Clock size={18} />Requisito aprobado y listo para exportar.</div>
        )}
      </section>
      <section className="space-y-4">
        {requirement.latest_version ? (
          <>
            <SpecEditor value={editedSpec} onChange={setEditedSpec} readonly={!canEdit} requirementId={requirement.id} />
            {requirement.latest_ai_review && <AIFeedbackPanel review={requirement.latest_ai_review} />}
          </>
        ) : (
          <div className="rounded-lg border border-silver bg-white p-10 text-center">
            <Bot className="mx-auto text-teal" size={42} />
            <h2 className="mt-3 text-lg font-semibold text-navy">Aun no hay especificacion generada</h2>
            <p className="mt-2 text-sm text-slate">Genera una especificacion con IA para habilitar revision e historial.</p>
          </div>
        )}
      </section>
    </div>
  );
}
