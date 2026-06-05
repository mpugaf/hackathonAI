import { Copy } from 'lucide-react';
import { useToast } from '../../context/AuthContext';

export default function SpecEditor({ value, onChange, readonly = false, label = 'Especificacion Generada' }) {
  const { showToast } = useToast();
  const copy = async () => {
    await navigator.clipboard.writeText(value || '');
    showToast('Copiado al portapapeles', 'success');
  };

  return (
    <section className="rounded-lg border border-silver bg-white p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-navy">{label}</h2>
          <p className="font-mono text-xs text-slate">{(value || '').length.toLocaleString('es-CL')} caracteres</p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`rounded px-2 py-1 font-mono text-xs font-semibold ${readonly ? 'bg-silver text-slate' : 'bg-teal-lt text-blue'}`}>
            {readonly ? 'Solo lectura' : 'Editable'}
          </span>
          {!readonly && (
            <button className="inline-flex items-center gap-2 rounded-md border border-silver px-3 py-2 text-sm font-semibold text-blue hover:bg-silver" onClick={copy}>
              <Copy size={15} />Copiar
            </button>
          )}
        </div>
      </div>
      <textarea
        className="min-h-[400px] w-full resize-y rounded-lg border border-silver bg-[#0d1b2e] p-4 font-mono text-[0.85rem] leading-6 text-[#c8d8f0] outline-none focus:border-2 focus:border-teal"
        value={value || ''}
        onChange={(event) => onChange?.(event.target.value)}
        readOnly={readonly}
      />
    </section>
  );
}
