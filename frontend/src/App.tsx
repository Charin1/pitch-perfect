// From: frontend/src/App.tsx
// ----------------------------------------
import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import DashboardPage from './pages/DashboardPage';
import LeadDetailPage from './pages/LeadDetailPage';
import Sidebar from './components/Sidebar';

function App() {
  return (
    <Router>
      <div className="flex h-screen bg-gray-100">
        <Sidebar />
        <div className="flex-1 flex flex-col overflow-hidden">
          <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-100">
            <div className="container mx-auto px-6 py-8">
              <Routes>
                <Route path="/" element={<DashboardPage />} />
                <Route path="/leads/:leadId" element={<LeadDetailPage />} />
              </Routes>
            </div>
          </main>
        </div>
      </div>
    </Router>
  );
}

export default App;