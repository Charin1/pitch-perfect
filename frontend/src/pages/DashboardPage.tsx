// From: frontend/src/pages/DashboardPage.tsx
// ----------------------------------------
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { getLeads } from '../api';
import LeadForm from '../components/LeadForm';
import LeadList from '../components/LeadList';

export default function DashboardPage() {
  const { data: leads, isLoading, error } = useQuery({
    queryKey: ['leads'],
    queryFn: getLeads,
  });

  const stats = {
    total: leads?.length || 0,
    completed: leads?.filter(l => l.status === 'COMPLETED').length || 0,
    pending: leads?.filter(l => ['PENDING', 'CRAWLING', 'ANALYZING'].includes(l.status)).length || 0,
  };

  return (
    <>
      <h1 className="text-3xl font-semibold text-gray-800 mb-6">Dashboard</h1>
      
      {/* Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="p-6 bg-white rounded-lg shadow-md">
          <h3 className="text-gray-500">Total Leads</h3>
          <p className="text-3xl font-bold text-gray-800">{stats.total}</p>
        </div>
        <div className="p-6 bg-white rounded-lg shadow-md">
          <h3 className="text-gray-500">Analysis Completed</h3>
          <p className="text-3xl font-bold text-green-600">{stats.completed}</p>
        </div>
        <div className="p-6 bg-white rounded-lg shadow-md">
          <h3 className="text-gray-500">Pending / In Progress</h3>
          <p className="text-3xl font-bold text-orange-600">{stats.pending}</p>
        </div>
      </div>

      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-2 text-gray-700">Add a New Lead</h2>
        <LeadForm />
      </div>

      <div>
        <h2 className="text-xl font-semibold mb-2 text-gray-700">Your Leads</h2>
        {isLoading && <p>Loading leads...</p>}
        {error && <p className="text-red-500">Failed to load leads: {error.message}</p>}
        {leads && <LeadList leads={leads} />}
      </div>
    </>
  );
}