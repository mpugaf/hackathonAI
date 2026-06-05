export default function LoadingOracle({ message = 'La IA esta procesando tu requisito...', isInline = false }) {
  const content = (
    <div className="flex items-center justify-center gap-3">
      <div className="flex gap-1" aria-hidden="true">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="h-2.5 w-2.5 rounded-full bg-teal"
            style={{ animation: 'pulse-dot 1.1s infinite ease-in-out', animationDelay: `${i * 140}ms` }}
          />
        ))}
      </div>
      <div>
        <p className="text-sm font-semibold text-white">{message}</p>
        <p className="text-xs text-teal">Esto puede tomar hasta 30 segundos</p>
      </div>
    </div>
  );

  if (isInline) {
    return <div className="rounded-md bg-navy px-4 py-3">{content}</div>;
  }

  return (
    <div className="absolute inset-0 z-30 flex items-center justify-center rounded-lg bg-white/70 backdrop-blur-sm">
      <div className="w-[min(360px,90%)] rounded-lg bg-navy p-6 shadow-xl">
        {content}
        <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-white/10">
          <div className="h-full w-1/2 rounded-full bg-teal" style={{ animation: 'progress-slide 1.2s infinite ease-in-out' }} />
        </div>
      </div>
    </div>
  );
}
