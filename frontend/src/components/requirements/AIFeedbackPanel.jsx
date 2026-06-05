import { Bot, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';

function scoreTone(score = 0) {
  if (score < 50) return ['text-danger', 'bg-red-50', 'bg-danger'];
  if (score < 70) return ['text-warn', 'bg-amber-50', 'bg-warn'];
  return ['text-ok', 'bg-emerald-50', 'bg-ok'];
}

export default function AIFeedbackPanel({ review }) {
  const [open, setOpen] = useState(true);
  if (!review) return null;
  const [textColor, bgColor, barColor] = scoreTone(review.ai_score);
  const decision = review.ai_score >= 70 ? 'PRE-APROBADO' : 'REQUIERE REVISION';

  return (
    <section className="overflow-hidden rounded-lg border border-silver bg-white">
      <button className="flex w-full items-center justify-between gap-3 p-4 text-left" onClick={() => setOpen((value) => !value)}>
        <div className="flex items-center gap-3">
          <Bot className="text-teal" size={22} />
          <div>
            <h2 className="text-sm font-semibold text-navy">Evaluacion del Revisor IA</h2>
            <p className="font-mono text-xs text-slate">{decision}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className={`flex h-11 w-11 items-center justify-center rounded-full font-mono text-sm font-semibold ${textColor} ${bgColor}`}>{review.ai_score ?? 0}</span>
          {open ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
        </div>
      </button>
      <div className={`transition-all duration-200 ${open ? 'max-h-[700px]' : 'max-h-0'} overflow-hidden`}>
        <div className="border-t border-silver p-4">
          <div className="h-2 overflow-hidden rounded-full bg-silver">
            <div className={`h-full ${barColor}`} style={{ width: `${review.ai_score ?? 0}%` }} />
          </div>
          <pre className="mt-4 whitespace-pre-wrap rounded-md bg-[#f8fafc] p-3 font-mono text-[0.83rem] leading-5 text-slate">{review.feedback}</pre>
          <p className="mt-3 text-xs text-slate">{new Date(review.created_at).toLocaleString('es-CL')}</p>
        </div>
      </div>
    </section>
  );
}
