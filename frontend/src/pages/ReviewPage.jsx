import { CheckCircle, XCircle } from 'lucide-react';
import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { approveRequirement, rejectRequirement } from '../api/requirements';
import AIFeedbackPanel from '../components/requirements/AIFeedbackPanel';
import SpecEditor from '../components/requirements/SpecEditor';
import ConfirmDialog from '../components/ui/ConfirmDialog';
import LoadingOracle from '../components/ui/LoadingOracle';
import StatusBadge from '../components/ui/StatusBadge';
import { useToast } from '../context/AuthContext';
import useRequirementDetail from '../hooks/useRequirementDetail';

export default function ReviewPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { showToast } = useToast();
  const { requirement, isLoading, error } = useRequirementDetail(id);
  const [comment, setComment] = useState('');
  const [confirm, setConfirm] = useState(null);
  const [isSaving, setIsSaving] = useState(false);

  const approve = async () => {
    setIsSaving(true);
    try {
      await approveRequirement(id);
      showToast('Requisito aprobado', 'success');
      navigate('/dashboard');
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setIsSaving(false);
      setConfirm(null);
    }
  };

  const reject = async () => {
    if (comment.trim().length < 3) {
      showToast('Agrega un comentario para rechazar.', 'warn');
      return;
    }
    setIsSaving(true);
    try {
      await rejectRequirement(id, comment.trim());
      showToast('Requisito devuelto al analista', 'success');
      navigate('/dashboard');
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setIsSaving(false);
      setConfirm(null);
    }
  };

  if (isLoading) return <LoadingOracle isInline message="Cargando revision..." />;
  if (error) return <p className="rounded-md bg-red-50 p-3 text-sm text-danger">{error}</p>;
  if (!requirement) return null;

  return (
    <div className="relative grid gap-5 lg:grid-cols-[0.8fr_1.2fr_1fr]">
      {isSaving && <LoadingOracle message="Guardando decision..." />}
      <section className="rounded-lg border border-silver bg-white p-4">
        <div className="flex items-start justify-between gap-3">
          <h2 className="text-base font-semibold text-navy">{requirement.title}</h2>
          <StatusBadge status={requirement.status} size="sm" />
        </div>
        <p className="mt-4 text-xs font-semibold uppercase text-slate">Requisito original</p>
        <pre className="mt-2 whitespace-pre-wrap rounded-md bg-[#f8fafc] p-3 font-mono text-xs leading-5 text-slate">{requirement.raw_input}</pre>
      </section>
      <SpecEditor value={requirement.latest_version?.generated_spec ?? ''} readonly />
      <section className="space-y-4">
        <AIFeedbackPanel review={requirement.latest_ai_review} />
        {requirement.status === 'en_revision' && (
          <div className="rounded-lg border border-silver bg-white p-4">
            <h2 className="text-base font-semibold text-navy">Tu Revision</h2>
            <textarea className="mt-3 min-h-32 w-full rounded-md border border-silver p-3 text-sm outline-none focus:border-teal" placeholder="Comentarios adicionales" value={comment} onChange={(e) => setComment(e.target.value)} />
            <div className="mt-4 flex flex-col gap-2 sm:flex-row">
              <button className="inline-flex items-center justify-center gap-2 rounded-md bg-ok px-4 py-2 text-sm font-semibold text-white" onClick={() => setConfirm('approve')}><CheckCircle size={16} />Aprobar</button>
              <button className="inline-flex items-center justify-center gap-2 rounded-md bg-danger px-4 py-2 text-sm font-semibold text-white" onClick={() => setConfirm('reject')}><XCircle size={16} />Rechazar y Devolver</button>
            </div>
          </div>
        )}
        {requirement.status === 'aprobado' && <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-[#065f46]">Este requisito fue aprobado.</div>}
        {requirement.status === 'rechazado' && <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-danger">Devuelto al analista.</div>}
      </section>
      {confirm === 'approve' && <ConfirmDialog title="Confirmar aprobacion" message="¿Confirmar aprobacion de este requisito?" confirmLabel="Aprobar" onCancel={() => setConfirm(null)} onConfirm={approve} />}
      {confirm === 'reject' && <ConfirmDialog title="Confirmar rechazo" message="¿Confirmar rechazo y devolucion al analista?" confirmLabel="Rechazar" variant="danger" onCancel={() => setConfirm(null)} onConfirm={reject} />}
    </div>
  );
}
