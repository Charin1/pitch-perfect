import React from 'react';
import { Link } from 'react-router-dom';
import { Lead } from '../api';

interface LeadListProps {
  leads: Lead[];
}

const statusColorMap = {
  PENDING: 'bg-gray-200 text-gray-800',
  CRAWLING: 'bg-blue-200 text-blue-800',
  ANALYZING: 'bg-yellow-200 text-yellow-800',
  COMPLETED: 'bg-green-200 text-green-800',
  FAILED: 'bg-red-200 text-red-800',
};

export default function LeadList({ leads }: LeadListProps) {
  if (!leads || leads.length === 0) {
    return <p className="text-center text-gray-500 py-4">No leads found. Add one to get started!</p>;
  }

  return (
    <div className="overflow-x-auto bg-white rounded-lg shadow">
      <table className="table w-full">
        <thead>
          <tr>
            <th>Company Name</th>
            <th>Website</th>
            <th>Status</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          {leads.map((lead) => (
            <tr key={lead.id} className="hover">
              <td>
                <Link to={`/leads/${lead.id}`} className="font-bold text-blue-600 hover:underline">
                  {lead.company_name}
                </Link>
              </td>
              <td>{lead.website_url}</td>
              <td>
                <span className={`px-2 py-1 text-xs font-semibold rounded-full ${statusColorMap[lead.status]}`}>
                  {lead.status}
                </span>
              </td>
              <td>{new Date(lead.created_at).toLocaleDateString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}