import { Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import DashboardPage from './pages/DashboardPage';
import DocumentsPage from './pages/DocumentsPage';
import DocumentDetailPage from './pages/DocumentDetailPage';

function Upload() {
  return <div className="p-6"><h1 className="text-2xl font-bold">Încărcare</h1></div>;
}

function Alerts() {
  return <div className="p-6"><h1 className="text-2xl font-bold">Alerte</h1></div>;
}

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/documents" element={<DocumentsPage />} />
        <Route path="/documents/:id" element={<DocumentDetailPage />} />
        <Route path="/upload" element={<Upload />} />
        <Route path="/alerts" element={<Alerts />} />
      </Route>
    </Routes>
  );
}
