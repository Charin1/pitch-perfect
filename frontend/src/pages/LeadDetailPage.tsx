// From: frontend/src/pages/LeadDetailPage.tsx
// ----------------------------------------
import React, { useState, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getLeadDetails, generatePitch } from '../api';
import PitchEditor from '../components/PitchEditor';

// Helper component for displaying the lead's status with appropriate colors and animation.
const StatusIndicator = ({ status }: { status: string }) => {
  const statusStyles: { [key: string]: string } = {
    PENDING: 'bg-gray-200 text-gray-800',
    CRAWLING: 'bg-blue-200 text-blue-800 animate-pulse',
    ANALYZING: 'bg-yellow-200 text-yellow-800 animate-pulse',
    COMPLETED: 'bg-green-200 text-green-800',
    FAILED: 'bg-red-200 text-red-800',
  };
  return (
    <span className={`px-3 py-1 text-sm font-semibold rounded-full ${statusStyles[status]}`}>
      {status}
    </span>
  );
};

export default function LeadDetailPage() {
  const { leadId } = useParams<{ leadId: string }>();
  const queryClient = useQueryClient();
  const [userProduct, setUserProduct] = useState("Our innovative B2B SaaS solution that boosts productivity.");
  
  const { data: lead, isLoading, error } = useQuery({
    queryKey: ['lead', leadId],
    queryFn: () => getLeadDetails(Number(leadId)),
    enabled: !!leadId,
    // This is the corrected refetchInterval logic for React Query v5.
    // It uses the 'query' object to access the data and determine if polling should continue.
    refetchInterval: (query) => {
      const data = query.state.data;
      const isProcessing = data?.status === 'PENDING' || data?.status === 'CRAWLING' || data?.status === 'ANALYZING';
      return isProcessing ? 5000 : false; // Poll every 5 seconds if in progress, otherwise stop.
    },
  });

  const mutation = useMutation({
    mutationFn: (productDesc: string) => generatePitch(Number(leadId), productDesc),
    onSuccess: () => {
      // In a more advanced app, you might refetch a list of pitches for this lead.
      // For now, the UI just displays the newly generated pitch.
      queryClient.invalidateQueries({ queryKey: ['pitches', leadId] });
    }
  });

  // Safely parse the bullet_points JSON string from the database.
  // useMemo ensures this only runs when the lead data changes.
  const bulletPoints = useMemo(() => {
    try {
      return lead?.bullet_points ? JSON.parse(lead.bullet_points) : [];
    } catch {
      // Return an empty array if parsing fails.
      return [];
    }
  }, [lead?.bullet_points]);

  // --- Render logic for different states ---
  if (isLoading) return <div className="p-8 text-center text-gray-600">Loading lead details...</div>;
  if (error) return <div className="p-8 text-center text-red-600">Error: {error.message}</div>;
  if (!lead) return <div className="p-8 text-center text-gray-600">Lead not found.</div>;

  return (
    <>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">{lead.company_name}</h1>
          <a href={lead.website_url} target="_blank" rel="noopener noreferrer" className="text-orange-600 hover:underline">
            {lead.website_url}
          </a>
        </div>
        <StatusIndicator status={lead.status} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
        {/* Left Column: AI-Generated Analysis */}
        <div className="lg:col-span-3">
          <div className="bg-white p-6 rounded-lg shadow-md min-h-[300px]">
            <h2 className="text-xl font-semibold text-gray-700 mb-4">AI-Generated Analysis</h2>
            
            {lead.status !== 'COMPLETED' && lead.status !== 'FAILED' && (
              <div className="text-center py-10">
                <p className="text-gray-600">Analysis in progress...</p>
                <p className="text-sm text-gray-400">(This page will auto-refresh)</p>
              </div>
            )}

            {lead.status === 'COMPLETED' && (
              <div>
                <h3 className="font-bold text-gray-800">Company Summary</h3>
                <p className="text-gray-600 mb-6 prose">{lead.summary}</p>
                
                <h3 className="font-bold text-gray-800">10 Key Business Points</h3>
                <ul className="list-disc list-inside mt-2 space-y-2 text-gray-600">
                  {bulletPoints.map((point: string, index: number) => (
                    <li key={index}>{point}</li>
                  ))}
                </ul>
              </div>
            )}

             {lead.status === 'FAILED' && (
              <div className="text-center py-10">
                <p className="text-red-600 font-bold">Analysis Failed</p>
                <p className="text-sm text-gray-500">Could not crawl or analyze the website. Please check the URL.</p>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Pitch Generation */}
        <div className="lg:col-span-2">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-xl font-semibold text-gray-700 mb-4">Generate a Pitch</h2>
            <div className="form-control w-full mb-4">
              <label className="label"><span className="label-text">Your Product/Service:</span></label>
              <textarea 
                value={userProduct} 
                onChange={e => setUserProduct(e.target.value)}
                className="textarea textarea-bordered w-full"
                rows={3}
                placeholder="Describe your product or service here..."
              />
            </div>
            <button 
              onClick={() => mutation.mutate(userProduct)} 
              disabled={mutation.isPending || lead.status !== 'COMPLETED'} 
              className="btn btn-primary bg-orange-600 hover:bg-orange-700 text-white w-full"
            >
              {mutation.isPending ? "Generating..." : "Generate Custom Pitch"}
            </button>
            
            {mutation.isSuccess && (
              <div className="mt-6">
                <h3 className="font-bold text-lg text-gray-800">Your New Pitch:</h3>
                <PitchEditor initial={mutation.data.content} />
              </div>
            )}
            {mutation.isError && (
                <p className="text-red-500 mt-2">Error generating pitch: {mutation.error.message}</p>
            )}
          </div>
        </div>
      </div>
    </>
  );
}