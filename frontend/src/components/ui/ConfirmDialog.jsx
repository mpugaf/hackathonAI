import { X } from 'lucide-react';

export default function ConfirmDialog({ title, message, confirmLabel = 'Confirmar', variant = 'primary', onCancel, onConfirm }) {
  const confirmClass = variant === 'danger' ? 'bg-danger text-white hover:bg-red-600' : 'bg-blue text-white hover:bg-navy';
  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-navy/45 px-4" role="dialog" aria-modal="true">
      <div className="w-full max-w-md rounded-lg bg-white p-5 shadow-xl">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold text-navy">{title}</h2>
            <p className="mt-2 text-sm text-slate">{message}</p>
          </div>
          <button className="rounded p-1 text-slate hover:bg-silver" onClick={onCancel} aria-label="Cerrar dialogo">
            <X size={18} />
          </button>
        </div>
        <div className="mt-5 flex justify-end gap-2">
          <button className="rounded-md border border-silver px-4 py-2 text-sm font-semibold text-slate hover:bg-silver" onClick={onCancel}>
            Cancelar
          </button>
          <button className={`rounded-md px-4 py-2 text-sm font-semibold ${confirmClass}`} onClick={onConfirm}>
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
