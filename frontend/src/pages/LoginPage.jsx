import { BrainCircuit } from 'lucide-react';
import { useState } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);

  if (isAuthenticated) return <Navigate to="/dashboard" replace />;

  const validate = () => {
    const next = {};
    if (!email || !email.includes('@')) next.email = 'Ingresa un email valido.';
    if (!password || password.length < 6) next.password = 'La contrasena debe tener al menos 6 caracteres.';
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const onSubmit = async (event) => {
    event.preventDefault();
    if (!validate()) return;
    setIsLoading(true);
    setErrors({});
    try {
      await login(email, password);
      navigate('/dashboard', { replace: true });
    } catch (err) {
      setErrors({ form: err.message });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen lg:grid lg:grid-cols-2">
      <section className="flex min-h-[320px] flex-col justify-between bg-navy p-8 text-white lg:min-h-screen lg:p-12">
        <div className="font-mono text-2xl font-semibold">ReqFlow <span className="text-teal">AI</span> <span className="rounded bg-teal px-2 py-1 text-xs text-navy">TCS AI Fridays</span></div>
        <div>
          <BrainCircuit size={48} className="mb-6 text-teal" />
          <h1 className="max-w-md text-4xl font-semibold leading-tight">Requisitos inteligentes. Aprobacion estructurada.</h1>
          <p className="mt-4 max-w-md text-[#b8c5db]">Gestiona especificaciones, revisiones IA y aprobaciones humanas con trazabilidad completa.</p>
        </div>
        <p className="text-sm text-[#7a90b8]">ReqFlow AI | Hackathon 2026</p>
      </section>
      <section className="flex items-center justify-center bg-[#f4f7fc] p-6">
        <form className="w-full max-w-md rounded-lg bg-white p-8 shadow-lg" onSubmit={onSubmit}>
          <h2 className="text-2xl font-semibold text-navy">Iniciar Sesion</h2>
          <p className="mt-1 text-sm text-slate">Ingresa con tus credenciales demo.</p>
          {errors.form && <p className="mt-4 rounded-md bg-red-50 p-3 text-sm font-medium text-danger">{errors.form}</p>}
          <label className="mt-6 block text-sm font-semibold text-navy">
            Email
            <input className="mt-2 w-full rounded-md border border-silver px-3 py-2 outline-none focus:border-teal" value={email} onChange={(e) => setEmail(e.target.value)} />
          </label>
          {errors.email && <p className="mt-1 text-sm text-danger">{errors.email}</p>}
          <label className="mt-4 block text-sm font-semibold text-navy">
            Password
            <input className="mt-2 w-full rounded-md border border-silver px-3 py-2 outline-none focus:border-teal" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          </label>
          {errors.password && <p className="mt-1 text-sm text-danger">{errors.password}</p>}
          <button className="mt-6 w-full rounded-md bg-blue px-4 py-3 font-semibold text-white hover:bg-navy disabled:opacity-60" disabled={isLoading}>
            {isLoading ? 'Validando...' : 'Iniciar Sesion'}
          </button>
        </form>
      </section>
    </main>
  );
}
