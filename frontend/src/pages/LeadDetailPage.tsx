// From: frontend/src/pages/LeadDetailPage.tsx
// ----------------------------------------
import React, { useState, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getLeadDetails, generatePitch } from '../api';
import PitchEditor from '../components/PitchEditor';

// --- TYPE DEFINITIONS for the data parsed from the analysis_json field ---
interface DetailedAnalysis {
  business_model: string;
  target_audience: string;
  value_proposition: string;
  company_tone: string;
  potential_needs: string[];
}
interface SwotAnalysis {
  strengths: string[];
  weaknesses: string[];
  opportunities: string[];
  threats: string[];
}
interface AnalysisData {
  summary: string;
  bullet_points: string[];
  simple_pitch: string;
  swot_analysis: SwotAnalysis;
  detailed_analysis: DetailedAnalysis;
}

// --- UI SUB-COMPONENTS ---

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

const OverviewPanel = ({ data }: { data: AnalysisData }) => (
  <div className="flex flex-col gap-8">
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h3 className="font-bold text-gray-800 mb-2 text-lg">Company Quick Summary</h3>
      <div className="max-h-48 overflow-y-auto pr-2 text-gray-600 prose">
        <p>{data.summary}</p>
      </div>
    </div>
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h3 className="font-bold text-gray-800 mb-2 text-lg">10 Key Business Points</h3>
      <div className="max-h-72 overflow-y-auto pr-2">
        <ul className="list-disc list-inside space-y-2 text-gray-600">
          {data.bullet_points?.map((point, index) => <li key={index}>{point}</li>)}
        </ul>
      </div>
    </div>
  </div>
);

const SwotPanel = ({ data }: { data: SwotAnalysis }) => (
  <div className="bg-white p-6 rounded-lg shadow-md">
    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
      <div>
        <h3 className="font-bold text-lg text-green-700 mb-2">Strengths</h3>
        <ul className="list-disc list-inside space-y-1 text-gray-600">
          {data.strengths?.map((point, i) => <li key={`s-${i}`}>{point}</li>)}
        </ul>
      </div>
      <div>
        <h3 className="font-bold text-lg text-red-700 mb-2">Weaknesses</h3>
        <ul className="list-disc list-inside space-y-1 text-gray-600">
          {data.weaknesses?.map((point, i) => <li key={`w-${i}`}>{point}</li>)}
        </ul>
      </div>
      <div>
        <h3 className="font-bold text-lg text-blue-700 mb-2">Opportunities</h3>
        <ul className="list-disc list-inside space-y-1 text-gray-600">
          {data.opportunities?.map((point, i) => <li key={`o-${i}`}>{point}</li>)}
        </ul>
      </div>
      <div>
        <h3 className="font-bold text-lg text-orange-600 mb-2">Threats</h3>
        <ul className="list-disc list-inside space-y-1 text-gray-600">
          {data.threats?.map((point, i) => <li key={`t-${i}`}>{point}</li>)}
        </ul>
      </div>
    </div>
  </div>
);

const DetailedAnalysisPanel = ({ data }: { data: DetailedAnalysis }) => (
  <div className="bg-white p-6 rounded-lg shadow-md">
    <div className="space-y-6 prose max-w-none text-gray-600">
      <div>
        <h3 className="font-bold text-gray-800 mt-0">Business Model</h3>
        <p>{data.business_model}</p>
      </div>
      <div>
        <h3 className="font-bold text-gray-800">Target Audience</h3>
        <p>{data.target_audience}</p>
      </div>
      <div>
        <h3 className="font-bold text-gray-800">Value Proposition</h3>
        <p>{data.value_proposition}</p>
      </div>
      <div>
        <h3 className="font-bold text-gray-800">Company Tone & Style</h3>
        <p>{data.company_tone}</p>
      </div>
      <div>
        <h3 className="font-bold text-orange-700">Potential Needs & Pain Points</h3>
        <ul className="list-disc list-inside">
          {data.potential_needs?.map((point, i) => <li key={`need-${i}`}>{point}</li>)}
        </ul>
      </div>
    </div>
  </div>
);


// --- MAIN PAGE COMPONENT ---
export default function LeadDetailPage() {
  const { leadId } = useParams<{ leadId: string }>();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('overview');
  const [userProduct, setUserProduct] = useState("Our innovative B2B SaaS solution that boosts productivity.");
  
  // This is the full, correct implementation of the useQuery hook
  const { data: lead, isLoading, error } = useQuery({
    queryKey: ['lead', leadId],
    queryFn: () => getLeadDetails(Number(leadId)),
    enabled: !!leadId,
    refetchInterval: (query) => {
      const data = query.state.data;
      const isProcessing = data?.status === 'PENDING' || data?.status === 'CRAWLING' || data?.status === 'ANALYZING';
      return isProcessing ? 5000 : false;
    },
  });

  // This is the full, correct implementation of the useMutation hook
  const mutation = useMutation({
    mutationFn: (productDesc: string) => generatePitch(Number(leadId), productDesc),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pitches', leadId] });
    }
  });

  // This is the full, correct implementation of the useMemo hook
  const analysisData: AnalysisData | null = useMemo(() => {
    try {
      return lead?.analysis_json ? JSON.parse(lead.analysis_json) : null;
    } catch {
      return null;
    }
  }, [lead?.analysis_json]);

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
        {/* Left/Middle Column: Tabbed Analysis Panel */}
        <div className="lg:col-span-3">
          <div role="tablist" className="tabs tabs-bordered mb-4">
            <a role="tab" className={`tab ${activeTab === 'overview' ? 'tab-active font-semibold' : ''}`} onClick={() => setActiveTab('overview')}>Overview</a>
            <a role="tab" className={`tab ${activeTab === 'detailed' ? 'tab-active font-semibold' : ''}`} onClick={() => setActiveTab('detailed')} disabled={!analysisData}>Detailed Analysis</a>
            <a role="tab" className={`tab ${activeTab === 'swot' ? 'tab-active font-semibold' : ''}`} onClick={() => setActiveTab('swot')} disabled={!analysisData}>SWOT Analysis</a>
          </div>
          
          {lead.status === 'COMPLETED' && analysisData ? (
            <div>
              {activeTab === 'overview' && <OverviewPanel data={analysisData} />}
              {activeTab === 'detailed' && <DetailedAnalysisPanel data={analysisData.detailed_analysis} />}
              {activeTab === 'swot' && <SwotPanel data={analysisData.swot_analysis} />}
            </div>
          ) : (
            <div className="bg-white p-6 rounded-lg shadow-md min-h-[300px] flex items-center justify-center">
              <div className="text-center">
                {lead.status === 'FAILED' ? (
                  <>
                    <p className="text-red-600 font-bold">Analysis Failed</p>
                    <p className="text-sm text-gray-500">Could not crawl or analyze the website.</p>
                  </>
                ) : (
                  <>
                    <p className="text-gray-600">Analysis in progress...</p>
                    <p className="text-sm text-gray-400">(This page will auto-refresh)</p>
                  </>
                )}
              </div>
            </div>
          )}
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