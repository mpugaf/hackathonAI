import { AlertTriangle, CheckCircle, Info, XCircle } from 'lucide-react';

const styles = {
  success: ['bg-[#d1fae5] text-[#065f46]', CheckCircle],
  error: ['bg-[#fee2e2] text-[#991b1b]', XCircle],
  warn: ['bg-[#fef3c7] text-[#b45309]', AlertTriangle],
  info: ['bg-[#dbeafe] text-[#1d4ed8]', Info]
};

export default function ToastHost({ toasts }) {
  return (
    <div className="fixed bottom-4 right-4 z-50 flex w-[min(360px,calc(100vw-2rem))] flex-col gap-3">
      {toasts.map((toast) => {
        const [classes, Icon] = styles[toast.type] ?? styles.info;
        return (
          <div key={toast.id} className={`toast-enter flex items-start gap-3 rounded-md border border-white/70 p-3 shadow-lg ${classes}`} role="status">
            <Icon size={18} className="mt-0.5 shrink-0" />
            <p className="text-sm font-medium">{toast.message}</p>
          </div>
        );
      })}
    </div>
  );
}
