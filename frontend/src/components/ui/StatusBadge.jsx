const map = {
  borrador: { bg: '#f1f5f9', text: '#475569', label: 'Borrador' },
  en_revision: { bg: '#fef3c7', text: '#b45309', label: 'En Revision' },
  aprobado: { bg: '#d1fae5', text: '#065f46', label: 'Aprobado' },
  rechazado: { bg: '#fee2e2', text: '#991b1b', label: 'Rechazado' }
};

export default function StatusBadge({ status, size = 'md' }) {
  const item = map[status] ?? map.borrador;
  return (
    <span
      className={`inline-flex items-center gap-1 rounded px-2 font-mono font-semibold ${size === 'sm' ? 'py-0.5 text-[0.65rem]' : 'py-1 text-[0.72rem]'}`}
      style={{ background: item.bg, color: item.text }}
    >
      <span aria-hidden="true">●</span>
      {item.label}
    </span>
  );
}
