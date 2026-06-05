import { ArrowLeft, Lightbulb } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createRequirement, listProjects } from '../api/requirements';
import { useToast } from '../context/AuthContext';

export default function NewRequirementPage() {
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [projects, setProjects] = useState([]);
  const [form, setForm] = useState({ title: '', rawInput: '', projectId: '' });
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const submitting = useRef(false);

  useEffect(() => {
    listProjects().then((items) => {
      setProjects(items);
      setForm((current) => ({ ...current, projectId: items[0]?.id ?? '' }));
    }).catch((err) => showToast(err.message, 'error'));
  }, [showToast]);

  const validate = () => {
    const next = {};
    if (form.title.length < 5 || form.title.length > 300) next.title = 'El titulo debe tener entre 5 y 300 caracteres.';
    if (form.rawInput.length < 20) next.rawInput = 'La descripcion debe tener al menos 20 caracteres.';
    if (!form.projectId) next.projectId = 'Selecciona un proyecto.';
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const onSubmit = async (event) => {
    event.preventDefault();
    if (submitting.current) return;
    if (!validate()) return;
    submitting.current = true;
    setIsLoading(true);
    try {
      await createRequirement({ project_id: form.projectId, title: form.title, raw_input: form.rawInput });
      showToast('Requisito creado exitosamente', 'success');
      navigate('/dashboard');
    } catch (err) {
      showToast(err.message, 'error');
      submitting.current = false;
      setIsLoading(false);
    }
  };

  return (
    <form className="max-w-4xl rounded-lg border border-silver bg-white p-5" onSubmit={onSubmit}>
      <label className="block text-sm font-semibold text-navy">
        Titulo del Requisito
        <input className="mt-2 w-full rounded-md border border-silver px-3 py-2 outline-none focus:border-teal" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
      </label>
      {errors.title && <p className="mt-1 text-sm text-danger">{errors.title}</p>}
      <label className="mt-5 block text-sm font-semibold text-navy">
        Proyecto
        <select className="mt-2 w-full rounded-md border border-silver px-3 py-2 outline-none focus:border-teal" value={form.projectId} onChange={(e) => setForm({ ...form, projectId: e.target.value })}>
          <option value="">Seleccionar proyecto</option>
          {projects.map((project) => <option key={project.id} value={project.id}>{project.title}</option>)}
        </select>
      </label>
      {errors.projectId && <p className="mt-1 text-sm text-danger">{errors.projectId}</p>}
      <label className="mt-5 block text-sm font-semibold text-navy">
        Descripcion del Requisito
        <textarea className="mt-2 min-h-[220px] w-full rounded-md border border-silver px-3 py-2 outline-none focus:border-teal" value={form.rawInput} onChange={(e) => setForm({ ...form, rawInput: e.target.value })} placeholder="Ej: Crear un modulo de catalogo de productos cosmeticos con filtros por categoria, precio y marca..." />
      </label>
      {errors.rawInput && <p className="mt-1 text-sm text-danger">{errors.rawInput}</p>}
      <div className="mt-4 flex items-start gap-2 rounded-md bg-teal-lt p-3 text-sm text-blue">
        <Lightbulb size={18} className="mt-0.5 shrink-0" />
        <p>Se especifico. Cuanto mas detalle proveas, mejor sera la especificacion generada por IA.</p>
      </div>
      <div className="mt-6 flex flex-wrap gap-3">
        <button className="rounded-md bg-blue px-4 py-2 text-sm font-semibold text-white hover:bg-navy disabled:opacity-60" disabled={isLoading}>{isLoading ? 'Creando...' : 'Crear Requisito'}</button>
        <button type="button" className="inline-flex items-center gap-2 rounded-md border border-silver px-4 py-2 text-sm font-semibold text-slate hover:bg-silver" onClick={() => navigate(-1)}>
          <ArrowLeft size={16} />Cancelar
        </button>
      </div>
    </form>
  );
}
