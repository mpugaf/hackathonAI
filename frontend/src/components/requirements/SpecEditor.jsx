import { marked } from 'marked';
import { Copy, Download, FileText, Pencil } from 'lucide-react';
import { useMemo, useState } from 'react';
import { useToast } from '../../context/AuthContext';
import { exportRequirementDocx } from '../../api/requirements';

marked.setOptions({ breaks: true, gfm: true });

const PROSE_CSS = `
  .spec-prose h1,.spec-prose h2,.spec-prose h3 { color:#1a3a6b; font-weight:700; margin-top:1.4em; margin-bottom:.4em; line-height:1.25; }
  .spec-prose h1 { font-size:1.25rem; border-bottom:2px solid #00c9b1; padding-bottom:.35em; }
  .spec-prose h2 { font-size:1.05rem; border-left:4px solid #1e6feb; padding-left:.6em; }
  .spec-prose h3 { font-size:.95rem; color:#1e6feb; }
  .spec-prose p  { margin:.55em 0; line-height:1.7; color:#0d1b2a; }
  .spec-prose ul,.spec-prose ol { padding-left:1.5em; margin:.5em 0; }
  .spec-prose li { margin:.3em 0; line-height:1.65; color:#0d1b2a; }
  .spec-prose li::marker { color:#00c9b1; font-weight:700; }
  .spec-prose strong { color:#1a3a6b; font-weight:700; }
  .spec-prose em { color:#5a6a85; }
  .spec-prose code { background:#f0f4fa; border-radius:4px; padding:.1em .35em; font-size:.85em; color:#1e6feb; font-family:monospace; }
  .spec-prose pre  { background:#0d1b2e; color:#c8d8f0; border-radius:8px; padding:1em; overflow-x:auto; font-size:.82rem; margin:.8em 0; }
  .spec-prose pre code { background:none; color:inherit; padding:0; }
  .spec-prose blockquote { border-left:4px solid #00c9b1; margin:.8em 0; padding:.5em 1em; background:#f0faf8; color:#1a3a6b; border-radius:0 6px 6px 0; }
  .spec-prose hr { border:none; border-top:1px solid #e2e8f0; margin:1.2em 0; }
  .spec-prose table { width:100%; border-collapse:collapse; margin:.8em 0; font-size:.9rem; }
  .spec-prose th { background:#1a3a6b; color:#fff; padding:.5em .75em; text-align:left; }
  .spec-prose td { border:1px solid #e2e8f0; padding:.4em .75em; }
  .spec-prose tr:nth-child(even) td { background:#f8fafc; }
`;

export default function SpecEditor({ value, onChange, readonly = false, label = 'Especificacion Generada', requirementId }) {
  const { showToast } = useToast();
  const [viewMode, setViewMode] = useState('rendered'); // 'rendered' | 'raw'
  const [downloading, setDownloading] = useState(false);

  const html = useMemo(() => {
    if (!value) return '';
    // Limpia prefijos de sección numerados tipo "1. HISTORIA DE USUARIO" → los convierte en h2
    const cleaned = value
      .replace(/^(\d{1,2})\.\s+([A-ZÁÉÍÓÚ\s]{4,})\s*$/gm, (_, n, title) => `## ${n}. ${title.trim()}`)
      .replace(/^#{1,6}\s*/gm, (m) => m); // ya son headings, ok
    return marked.parse(cleaned);
  }, [value]);

  const copy = async () => {
    await navigator.clipboard.writeText(value || '');
    showToast('Copiado al portapapeles', 'success');
  };

  const downloadDocx = async () => {
    if (!requirementId || downloading) return;
    setDownloading(true);
    try {
      const blob = await exportRequirementDocx(requirementId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `especificacion_${requirementId}.docx`;
      a.click();
      URL.revokeObjectURL(url);
      showToast('Documento descargado', 'success');
    } catch {
      showToast('Error al descargar el documento', 'error');
    } finally {
      setDownloading(false);
    }
  };

  const isRendered = viewMode === 'rendered';

  return (
    <section className="rounded-lg border border-silver bg-white p-4">
      <style>{PROSE_CSS}</style>

      {/* Header */}
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-navy">{label}</h2>
          <p className="font-mono text-xs text-slate">{(value || '').length.toLocaleString('es-CL')} caracteres</p>
        </div>
        <div className="flex items-center gap-2">
          {/* Toggle vista */}
          <div className="flex overflow-hidden rounded-md border border-silver text-xs font-semibold">
            <button
              type="button"
              className={`flex items-center gap-1 px-3 py-1.5 ${isRendered ? 'bg-blue text-white' : 'text-slate hover:bg-silver'}`}
              onClick={() => setViewMode('rendered')}
            >
              <FileText size={13} />Vista
            </button>
            <button
              type="button"
              className={`flex items-center gap-1 px-3 py-1.5 ${!isRendered ? 'bg-blue text-white' : 'text-slate hover:bg-silver'}`}
              onClick={() => setViewMode('raw')}
            >
              <Pencil size={13} />{readonly ? 'Texto' : 'Editar'}
            </button>
          </div>
          <button
            type="button"
            className="inline-flex items-center gap-2 rounded-md border border-silver px-3 py-1.5 text-xs font-semibold text-blue hover:bg-silver"
            onClick={copy}
          >
            <Copy size={13} />Copiar
          </button>
          {requirementId && (
            <button
              type="button"
              disabled={downloading}
              className="inline-flex items-center gap-2 rounded-md bg-teal px-3 py-1.5 text-xs font-semibold text-white hover:opacity-90 disabled:opacity-50"
              onClick={downloadDocx}
            >
              <Download size={13} />{downloading ? 'Descargando…' : 'Descargar DOCX'}
            </button>
          )}
        </div>
      </div>

      {/* Contenido */}
      {isRendered ? (
        <div
          className="spec-prose min-h-[400px] max-h-[72vh] overflow-y-auto rounded-lg border border-silver bg-white px-6 py-5"
          dangerouslySetInnerHTML={{ __html: html || '<p style="color:#5a6a85;font-style:italic">Sin contenido aún.</p>' }}
        />
      ) : (
        <textarea
          className="min-h-[400px] w-full resize-y rounded-lg border border-silver bg-[#0d1b2e] p-4 font-mono text-[0.82rem] leading-6 text-[#c8d8f0] outline-none focus:border-2 focus:border-teal"
          value={value || ''}
          onChange={(e) => onChange?.(e.target.value)}
          readOnly={readonly}
        />
      )}
    </section>
  );
}
