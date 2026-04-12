import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';

// Lazy-loaded pages would go here; for now use placeholder components
function Dashboard() {
  return <div className="p-6"><h1 className="text-2xl font-bold">Panou de Control</h1></div>;
}

function Documents() {
  return <div className="p-6"><h1 className="text-2xl font-bold">Documente</h1></div>;
}

function DocumentDetail() {
  return <div className="p-6"><h1 className="text-2xl font-bold">Detalii Document</h1></div>;
}

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
        <Route path="/" element={<Dashboard />} />
        <Route path="/documents" element={<Documents />} />
        <Route path="/documents/:id" element={<DocumentDetail />} />
        <Route path="/upload" element={<Upload />} />
        <Route path="/alerts" element={<Alerts />} />
      </Route>
    </Routes>
  );
}
