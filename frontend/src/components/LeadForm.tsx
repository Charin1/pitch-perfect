import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createLead } from '../api';

export default function LeadForm() {
  const [companyName, setCompanyName] = useState('');
  const [websiteUrl, setWebsiteUrl] = useState('');
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: createLead,
    onSuccess: () => {
      // Invalidate and refetch the leads query to show the new lead
      queryClient.invalidateQueries({ queryKey: ['leads'] });
      setCompanyName('');
      setWebsiteUrl('');
    },
    onError: (error) => {
      alert(`Failed to create lead: ${error.message}`);
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!companyName || !websiteUrl) {
      alert('Please fill in both fields.');
      return;
    }
    mutation.mutate({ company_name: companyName, website_url: websiteUrl });
  };

  return (
    <form onSubmit={handleSubmit} className="p-4 bg-white rounded-lg shadow">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <input
          type="text"
          value={companyName}
          onChange={(e) => setCompanyName(e.target.value)}
          placeholder="Company Name"
          className="input input-bordered w-full"
        />
        <input
          type="url"
          value={websiteUrl}
          onChange={(e) => setWebsiteUrl(e.target.value)}
          placeholder="https://example.com"
          className="input input-bordered w-full"
        />
      </div>
      <button type="submit" className="btn btn-primary mt-4 w-full md:w-auto" disabled={mutation.isPending}>
        {mutation.isPending ? 'Adding Lead...' : 'Add Lead'}
      </button>
    </form>
  );
}