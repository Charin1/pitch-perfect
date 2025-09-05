// From: frontend/src/components/LeadForm.tsx
// ----------------------------------------
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
      queryClient.invalidateQueries({ queryKey: ['leads'] });
      setCompanyName('');
      setWebsiteUrl('');
    },
    onError: (error: any) => {
      // Provide a more helpful error message to the user
      const errorDetail = error.response?.data?.detail || error.message;
      alert(`Failed to create lead: ${JSON.stringify(errorDetail)}`);
    }
  });

  // --- NEW, SMARTER SUBMIT HANDLER ---
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!companyName || !websiteUrl) {
      alert('Please fill in both fields.');
      return;
    }

    let formattedUrl = websiteUrl.trim();
    // If the URL doesn't start with http:// or https://, prepend https://
    if (!/^https?:\/\//i.test(formattedUrl)) {
      formattedUrl = `https://${formattedUrl}`;
    }

    mutation.mutate({ company_name: companyName, website_url: formattedUrl });
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
          required
        />
        <input
          type="text" // Using text is more flexible than 'url' for our formatter
          value={websiteUrl}
          onChange={(e) => setWebsiteUrl(e.target.value)}
          placeholder="example.com"
          className="input input-bordered w-full"
          required
        />
      </div>
      <button type="submit" className="btn btn-primary bg-orange-600 hover:bg-orange-700 text-white mt-4 w-full md:w-auto" disabled={mutation.isPending}>
        {mutation.isPending ? 'Adding Lead...' : 'Add Lead'}
      </button>
    </form>
  );
}