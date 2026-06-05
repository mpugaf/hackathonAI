import { useLocation } from 'react-router-dom';

const titles = [
  [/^\/dashboard/, 'Dashboard'],
  [/^\/requirements\/new/, 'Nuevo Requisito'],
  [/^\/requirements\/.+\/review/, 'Revision de Requisito'],
  [/^\/requirements\/.+\/history/, 'Historial de Versiones'],
  [/^\/requirements\/.+/, 'Detalle de Requisito']
];

export default function TopBar() {
  const location = useLocation();
  const title = titles.find(([pattern]) => pattern.test(location.pathname))?.[1] ?? 'ReqFlow AI';
  return (
    <header className="border-b border-silver bg-white px-5 py-4 lg:px-8">
      <h1 className="text-xl font-semibold text-navy">{title}</h1>
    </header>
  );
}
