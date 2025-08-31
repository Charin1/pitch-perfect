// From: frontend/src/components/LeadList.tsx
// ----------------------------------------
import React from 'react';
import { Link } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Lead, deleteLead } from '../api'; // <-- Import deleteLead

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
  const queryClient = useQueryClient();

  // Set up a mutation for deleting a lead
  const deleteMutation = useMutation({
    mutationFn: deleteLead,
    onSuccess: () => {
      // When a delete is successful, invalidate the 'leads' query.
      // This tells React Query to automatically refetch the list of leads.
      queryClient.invalidateQueries({ queryKey: ['leads'] });
    },
    onError: (error) => {
      // Simple error handling
      alert(`Failed to delete lead: ${error.message}`);
    }
  });

  const handleDelete = (leadId: number) => {
    // It's good practice to confirm a destructive action.
    if (window.confirm('Are you sure you want to permanently delete this lead?')) {
      deleteMutation.mutate(leadId);
    }
  };

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
            <th className="text-right">Actions</th> {/* <-- Add Actions column header */}
          </tr>
        </thead>
        <tbody>
          {leads.map((lead) => (
            <tr key={lead.id} className="hover">
              <td>
                <Link to={`/leads/${lead.id}`} className="font-bold text-orange-600 hover:underline">
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
              <td className="text-right"> {/* <-- Add Actions cell */}
                <button 
                  onClick={() => handleDelete(lead.id)}
                  // Disable the button for the specific lead being deleted to prevent double clicks
                  disabled={deleteMutation.isPending && deleteMutation.variables === lead.id}
                  className="btn btn-xs btn-error btn-outline"
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}