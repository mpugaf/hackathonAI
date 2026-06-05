import { Download, Loader2 } from 'lucide-react';
import { useState } from 'react';
import { exportRequirement } from '../../api/requirements';
import { useToast } from '../../context/AuthContext';

export default function ExportButton({ requirementId }) {
  const [isLoading, setIsLoading] = useState(false);
  const { showToast } = useToast();

  const onClick = async () => {
    setIsLoading(true);
    try {
      const blob = await exportRequirement(requirementId);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = `spec_${requirementId}.html`;
      anchor.click();
      URL.revokeObjectURL(url);
      showToast('Especificacion exportada exitosamente', 'success');
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <button className="inline-flex items-center justify-center gap-2 rounded-md border border-teal px-4 py-2 text-sm font-semibold text-blue hover:bg-teal-lt" onClick={onClick} disabled={isLoading}>
      {isLoading ? <Loader2 size={17} className="animate-spin" /> : <Download size={17} />}
      {isLoading ? 'Exportando...' : 'Exportar Especificacion'}
    </button>
  );
}
