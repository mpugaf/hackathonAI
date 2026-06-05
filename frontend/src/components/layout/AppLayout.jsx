import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopBar from './TopBar';

export default function AppLayout() {
  return (
    <div className="min-h-screen lg:flex">
      <div className="lg:fixed lg:inset-y-0 lg:left-0">
        <Sidebar />
      </div>
      <div className="min-w-0 flex-1 lg:ml-60">
        <TopBar />
        <main className="px-4 py-5 sm:px-6 lg:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
