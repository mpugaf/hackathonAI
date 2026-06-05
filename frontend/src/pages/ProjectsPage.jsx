import { FolderOpen, Pencil, Plus, Save, Trash2, X } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { createProject, deleteProject, listProjects, updateProject } from '../api/projects';
import { useToast } from '../context/AuthContext';

function ProjectForm({ initial = {}, onSave, onCancel, isSaving }) {
  const [title, setTitle] = useState(initial.title ?? '');
  const [description, setDescription] = useState(initial.description ?? '');
  const titleRef = useRef(null);

  useEffect(() => { titleRef.current?.focus(); }, []);

  const submit = (e) => {
    e.preventDefault();
    if (title.trim().length < 5) return;
    onSave({ title: title.trim(), description: description.trim() || null });
  };

  return (
    <form onSubmit={submit} className="rounded-lg border border-blue/30 bg-blue/5 p-5 space-y-4">
      <h3 className="text-sm font-bold text-navy">{initial.id ? 'Editar proyecto' : 'Nuevo proyecto'}</h3>
      <div>
        <label className="block text-xs font-semibold text-slate mb-1">Nombre <span className="text-danger">*</span></label>
        <input
          ref={titleRef}
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          minLength={5}
          maxLength={200}
          required
          placeholder="Ej: Sistema de Facturación"
          className="w-full rounded-md border border-silver px-3 py-2 text-sm text-navy placeholder:text-slate focus:border-blue focus:outline-none"
        />
        {title.length > 0 && title.trim().length < 5 && (
          <p className="mt-1 text-xs text-danger">Mínimo 5 caracteres</p>
        )}
      </div>
      <div>
        <label className="block text-xs font-semibold text-slate mb-1">Descripción</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          placeholder="Descripción opcional del proyecto…"
          className="w-full rounded-md border border-silver px-3 py-2 text-sm text-navy placeholder:text-slate focus:border-blue focus:outline-none resize-none"
        />
      </div>
      <div className="flex gap-2 justify-end">
        <button
          type="button"
          onClick={onCancel}
          className="inline-flex items-center gap-1.5 rounded-md border border-silver px-4 py-2 text-sm font-semibold text-slate hover:bg-silver"
        >
          <X size={14} />Cancelar
        </button>
        <button
          type="submit"
          disabled={isSaving || title.trim().length < 5}
          className="inline-flex items-center gap-1.5 rounded-md bg-blue px-4 py-2 text-sm font-semibold text-white hover:opacity-90 disabled:opacity-50"
        >
          <Save size={14} />{isSaving ? 'Guardando…' : 'Guardar'}
        </button>
      </div>
    </form>
  );
}

function ConfirmDeleteDialog({ project, onConfirm, onCancel }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-sm rounded-xl bg-white p-6 shadow-xl">
        <h2 className="text-base font-bold text-navy">Eliminar proyecto</h2>
        <p className="mt-2 text-sm text-slate">
          ¿Eliminar <span className="font-semibold text-navy">"{project.title}"</span>?
          Esta acción no se puede deshacer.
        </p>
        <div className="mt-5 flex justify-end gap-2">
          <button
            onClick={onCancel}
            className="rounded-md border border-silver px-4 py-2 text-sm font-semibold text-slate hover:bg-silver"
          >Cancelar</button>
          <button
            onClick={onConfirm}
            className="rounded-md bg-danger px-4 py-2 text-sm font-semibold text-white hover:opacity-90"
          >Eliminar</button>
        </div>
      </div>
    </div>
  );
}

export default function ProjectsPage() {
  const { showToast } = useToast();
  const [projects, setProjects] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingProject, setEditingProject] = useState(null);
  const [deletingProject, setDeletingProject] = useState(null);
  const [isSaving, setIsSaving] = useState(false);

  const load = async () => {
    setIsLoading(true);
    try {
      setProjects(await listProjects());
    } catch {
      showToast('Error al cargar proyectos', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async (payload) => {
    setIsSaving(true);
    try {
      const created = await createProject(payload);
      setProjects((prev) => [created, ...prev]);
      setShowForm(false);
      showToast('Proyecto creado', 'success');
    } catch (err) {
      showToast(err.message ?? 'Error al crear proyecto', 'error');
    } finally {
      setIsSaving(false);
    }
  };

  const handleUpdate = async (payload) => {
    setIsSaving(true);
    try {
      const updated = await updateProject(editingProject.id, payload);
      setProjects((prev) => prev.map((p) => (p.id === updated.id ? updated : p)));
      setEditingProject(null);
      showToast('Proyecto actualizado', 'success');
    } catch (err) {
      showToast(err.message ?? 'Error al actualizar proyecto', 'error');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async () => {
    try {
      await deleteProject(deletingProject.id);
      setProjects((prev) => prev.filter((p) => p.id !== deletingProject.id));
      setDeletingProject(null);
      showToast('Proyecto eliminado', 'success');
    } catch (err) {
      showToast(err.response?.data?.detail ?? 'No se puede eliminar: tiene requisitos asociados', 'error');
      setDeletingProject(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-navy">Proyectos</h1>
          <p className="text-sm text-slate">{projects.length} proyecto{projects.length !== 1 ? 's' : ''} activo{projects.length !== 1 ? 's' : ''}</p>
        </div>
        {!showForm && !editingProject && (
          <button
            onClick={() => setShowForm(true)}
            className="inline-flex items-center gap-2 rounded-md bg-blue px-4 py-2 text-sm font-semibold text-white hover:opacity-90"
          >
            <Plus size={16} />Nuevo Proyecto
          </button>
        )}
      </div>

      {/* Formulario crear */}
      {showForm && (
        <ProjectForm
          onSave={handleCreate}
          onCancel={() => setShowForm(false)}
          isSaving={isSaving}
        />
      )}

      {/* Lista */}
      {isLoading ? (
        <div className="py-16 text-center text-sm text-slate">Cargando proyectos…</div>
      ) : projects.length === 0 ? (
        <div className="rounded-lg border border-silver bg-white py-16 text-center">
          <FolderOpen size={40} className="mx-auto mb-3 text-slate/40" />
          <p className="text-sm font-semibold text-slate">Aún no hay proyectos</p>
          <p className="text-xs text-slate/70 mt-1">Crea el primero usando el botón "Nuevo Proyecto"</p>
        </div>
      ) : (
        <div className="space-y-3">
          {projects.map((project) => (
            <div key={project.id}>
              {editingProject?.id === project.id ? (
                <ProjectForm
                  initial={project}
                  onSave={handleUpdate}
                  onCancel={() => setEditingProject(null)}
                  isSaving={isSaving}
                />
              ) : (
                <article className="rounded-lg border border-silver bg-white p-5 transition hover:shadow-sm">
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <FolderOpen size={16} className="shrink-0 text-blue" />
                        <h2 className="truncate text-sm font-bold text-navy">{project.title}</h2>
                      </div>
                      {project.description && (
                        <p className="mt-1.5 text-sm text-slate leading-relaxed">{project.description}</p>
                      )}
                      <p className="mt-2 text-xs text-slate/60">
                        Creado el {new Date(project.created_at).toLocaleDateString('es-CL', { day: '2-digit', month: 'short', year: 'numeric' })}
                      </p>
                    </div>
                    <div className="flex shrink-0 items-center gap-2">
                      <button
                        onClick={() => { setShowForm(false); setEditingProject(project); }}
                        className="inline-flex items-center gap-1.5 rounded-md border border-silver px-3 py-1.5 text-xs font-semibold text-slate hover:bg-silver"
                      >
                        <Pencil size={13} />Editar
                      </button>
                      <button
                        onClick={() => setDeletingProject(project)}
                        className="inline-flex items-center gap-1.5 rounded-md border border-red-200 px-3 py-1.5 text-xs font-semibold text-danger hover:bg-red-50"
                      >
                        <Trash2 size={13} />Eliminar
                      </button>
                    </div>
                  </div>
                </article>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Dialog eliminar */}
      {deletingProject && (
        <ConfirmDeleteDialog
          project={deletingProject}
          onConfirm={handleDelete}
          onCancel={() => setDeletingProject(null)}
        />
      )}
    </div>
  );
}
