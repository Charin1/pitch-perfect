// From: frontend/src/pages/LeadDetailPage.tsx
// ----------------------------------------
import React, { useState, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getLeadDetails, generatePitch, Lead } from '../api';
import PitchEditor from '../components/PitchEditor';

// --- TYPE DEFINITIONS for the data parsed from the analysis_json field ---
interface KeyPerson {
  name: string;
  title: string;
}
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
interface TechAndTrends {
  recurring_themes: string[];
  market_trends: string[];
  thought_leadership_position: string;
}
interface GrowthAnalysis {
    funding_summary: string;
    revenue_estimate: string;
    stability_rating: number | string;
    report: string;
}
interface AnalysisData {
  summary?: string;
  bullet_points?: string[];
  simple_pitch?: string;
  swot_analysis?: SwotAnalysis;
  detailed_analysis?: DetailedAnalysis;
  key_persons?: KeyPerson[];
  tech_and_trends?: TechAndTrends;
  growth_analysis?: GrowthAnalysis;
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
        <p>{data.summary || 'No summary available.'}</p>
      </div>
    </div>
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h3 className="font-bold text-gray-800 mb-2 text-lg">10 Key Business Points</h3>
      <div className="max-h-72 overflow-y-auto pr-2">
        <ul className="list-disc list-inside space-y-2 text-gray-600">
          {data.bullet_points?.map((point, index) => <li key={index}>{point}</li>) || <li>No data available.</li>}
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
          {data?.strengths?.map((point, i) => <li key={`s-${i}`}>{point}</li>) || <li>N/A</li>}
        </ul>
      </div>
      <div>
        <h3 className="font-bold text-lg text-red-700 mb-2">Weaknesses</h3>
        <ul className="list-disc list-inside space-y-1 text-gray-600">
          {data?.weaknesses?.map((point, i) => <li key={`w-${i}`}>{point}</li>) || <li>N/A</li>}
        </ul>
      </div>
      <div>
        <h3 className="font-bold text-lg text-blue-700 mb-2">Opportunities</h3>
        <ul className="list-disc list-inside space-y-1 text-gray-600">
          {data?.opportunities?.map((point, i) => <li key={`o-${i}`}>{point}</li>) || <li>N/A</li>}
        </ul>
      </div>
      <div>
        <h3 className="font-bold text-lg text-orange-600 mb-2">Threats</h3>
        <ul className="list-disc list-inside space-y-1 text-gray-600">
          {data?.threats?.map((point, i) => <li key={`t-${i}`}>{point}</li>) || <li>N/A</li>}
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
        <p>{data?.business_model || 'N/A'}</p>
      </div>
      <div>
        <h3 className="font-bold text-gray-800">Target Audience</h3>
        <p>{data?.target_audience || 'N/A'}</p>
      </div>
      <div>
        <h3 className="font-bold text-gray-800">Value Proposition</h3>
        <p>{data?.value_proposition || 'N/A'}</p>
      </div>
      <div>
        <h3 className="font-bold text-gray-800">Company Tone & Style</h3>
        <p>{data?.company_tone || 'N/A'}</p>
      </div>
      <div>
        <h3 className="font-bold text-orange-700">Potential Needs & Pain Points</h3>
        <ul className="list-disc list-inside">
          {data?.potential_needs?.map((point, i) => <li key={`need-${i}`}>{point}</li>) || <li>No data available.</li>}
        </ul>
      </div>
    </div>
  </div>
);

const KeyPersonsPanel = ({ data }: { data: KeyPerson[] }) => (
  <div className="bg-white p-6 rounded-lg shadow-md">
    {data && data.length > 0 ? (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {data.map((person, index) => (
          <div key={index} className="flex items-center gap-4 p-4 border rounded-lg bg-gray-50">
            <div className="avatar placeholder">
              <div className="bg-orange-600 text-white rounded-full w-12">
                <span className="text-xl">{person.name.charAt(0)}</span>
              </div>
            </div>
            <div>
              <p className="font-bold text-gray-800">{person.name}</p>
              <p className="text-sm text-gray-600">{person.title}</p>
            </div>
          </div>
        ))}
      </div>
    ) : (
      <div className="text-center py-10">
        <p className="text-gray-600">No C-suite or key persons found on the website.</p>
        <p className="text-sm text-gray-400">The AI may not have found a dedicated team page.</p>
      </div>
    )}
  </div>
);

const TechTrendsPanel = ({ data }: { data: TechAndTrends }) => {
    const ThemeDisplay = ({ theme }: { theme: string }) => {
        const match = theme.match(/(.*?)\s*\((.*)\)/);

        return (
            <div className="p-4 border rounded-lg bg-gray-50 flex flex-col justify-center">
                {match ? (
                    <>
                        <h4 className="font-bold text-gray-800 text-center">{match[1].trim()}</h4>
                        <div className="flex flex-wrap gap-2 mt-2 justify-center">
                            {match[2].split(',').map(d => d.trim()).map((detail, i) => (
                                <span key={i} className="badge badge-sm">{detail}</span>
                            ))}
                        </div>
                    </>
                ) : (
                    <h4 className="font-bold text-gray-800 text-center">{theme}</h4>
                )}
            </div>
        );
    };

    return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <div className="space-y-8">
        <div>
          <h3 className="font-bold text-gray-800 text-lg">Strategic Focus & Keywords</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
            {data?.recurring_themes?.length > 0 ? (
              data.recurring_themes.map((theme, i) => (
                <ThemeDisplay key={`theme-${i}`} theme={theme} />
              ))
            ) : (
              <p className="text-sm text-gray-500 col-span-2">No specific themes identified.</p>
            )}
          </div>
        </div>
        <div>
          <h3 className="font-bold text-gray-800 text-lg">Key Market Trends</h3>
          <ul className="list-disc list-inside space-y-1 text-gray-600 mt-2">
            {data?.market_trends?.map((trend, i) => <li key={`trend-${i}`}>{trend}</li>) || <li>No data available.</li>}
          </ul>
        </div>
        <div>
          <h3 className="font-bold text-gray-800 text-lg">Thought Leadership Position</h3>
          <p className="italic text-gray-600 mt-2">"{data?.thought_leadership_position || 'N/A'}"</p>
        </div>
      </div>
    </div>
  );
};

const GrowthAnalysisPanel = ({ data }: { data: GrowthAnalysis }) => {
    const getRatingColor = (rating: number) => {
      if (rating <= 3) return 'bg-red-500';
      if (rating <= 6) return 'bg-yellow-500';
      return 'bg-green-500';
    };

    const rating = data?.stability_rating;
    const validatedRating = (typeof rating === 'number' && !isNaN(rating)) ? rating : 0;
    const ratingText = `${validatedRating} / 10`;
  
    return (
      <div className="bg-white p-6 rounded-lg shadow-md">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-center mb-6">
          <div className="p-4 border rounded-lg flex flex-col justify-center">
            <h4 className="font-bold text-gray-500 text-sm uppercase tracking-wider">Funding</h4>
            <p className="text-xl font-semibold text-gray-800 mt-1">{data?.funding_summary || 'N/A'}</p>
          </div>
          <div className="p-4 border rounded-lg flex flex-col justify-center">
            <h4 className="font-bold text-gray-500 text-sm uppercase tracking-wider">Est. Revenue</h4>
            <p className="text-xl font-semibold text-gray-800 mt-1">{data?.revenue_estimate || 'N/A'}</p>
          </div>
          <div className="p-4 border rounded-lg">
            <h4 className="font-bold text-gray-500 text-sm uppercase tracking-wider">Stability Rating</h4>
            <div className="relative w-full bg-gray-200 rounded-full h-6 mt-2">
              <div 
                className={`h-full rounded-full ${getRatingColor(validatedRating)} transition-all duration-500`} 
                style={{ width: `${validatedRating * 10}%` }}
              />
              <div className="absolute inset-0 flex items-center justify-center">
                <span 
                  className={`font-bold text-sm ${validatedRating < 4 ? 'text-gray-700' : 'text-white'}`}
                >
                  {ratingText}
                </span>
              </div>
            </div>
          </div>
        </div>
        <div>
          <h3 className="font-bold text-gray-800 text-lg">Analyst Report</h3>
          <p className="prose max-w-none text-gray-600 mt-2">{data?.report || 'No report available.'}</p>
        </div>
      </div>
    );
};

// --- MAIN PAGE COMPONENT ---
export default function LeadDetailPage() {
  const { leadId } = useParams<{ leadId: string }>();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('overview');
  const [userProduct, setUserProduct] = useState("Our innovative B2B SaaS solution that boosts productivity.");
  
  const { data: lead, isLoading, error } = useQuery<Lead>({
    queryKey: ['lead', leadId],
    queryFn: () => getLeadDetails(Number(leadId)),
    enabled: !!leadId,
    refetchInterval: (query) => {
      const data = query.state.data;
      const isProcessing = data?.status === 'PENDING' || data?.status === 'CRAWLING' || data?.status === 'ANALYZING';
      return isProcessing ? 5000 : false;
    },
  });

  const mutation = useMutation({
    mutationFn: (productDesc: string) => generatePitch(Number(leadId!), productDesc),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pitches', leadId] });
    }
  });

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
            <a role="tab" className={`tab ${activeTab === 'growth' ? 'tab-active font-semibold' : ''} ${!analysisData ? 'tab-disabled' : ''}`} onClick={() => analysisData && setActiveTab('growth')}>Growth Analysis</a>
            <a role="tab" className={`tab ${activeTab === 'detailed' ? 'tab-active font-semibold' : ''} ${!analysisData ? 'tab-disabled' : ''}`} onClick={() => analysisData && setActiveTab('detailed')}>Detailed Analysis</a>
            <a role="tab" className={`tab ${activeTab === 'swot' ? 'tab-active font-semibold' : ''} ${!analysisData ? 'tab-disabled' : ''}`} onClick={() => analysisData && setActiveTab('swot')}>SWOT</a>
            <a role="tab" className={`tab ${activeTab === 'persons' ? 'tab-active font-semibold' : ''} ${!analysisData ? 'tab-disabled' : ''}`} onClick={() => analysisData && setActiveTab('persons')}>Key Persons</a>
            <a role="tab" className={`tab ${activeTab === 'tech' ? 'tab-active font-semibold' : ''} ${!analysisData ? 'tab-disabled' : ''}`} onClick={() => analysisData && setActiveTab('tech')}>Tech & Trends</a>
          </div>
          
          {lead.status === 'COMPLETED' && analysisData ? (
            <div>
              {activeTab === 'overview' && <OverviewPanel data={analysisData} />}
              
              {activeTab === 'growth' && analysisData.growth_analysis && 
                <GrowthAnalysisPanel data={analysisData.growth_analysis} />}

              {activeTab === 'detailed' && analysisData.detailed_analysis && 
                <DetailedAnalysisPanel data={analysisData.detailed_analysis} />}

              {activeTab === 'swot' && analysisData.swot_analysis && 
                <SwotPanel data={analysisData.swot_analysis} />}

              {activeTab === 'persons' && analysisData.key_persons && 
                <KeyPersonsPanel data={analysisData.key_persons} />}

              {activeTab === 'tech' && analysisData.tech_and_trends && 
                <TechTrendsPanel data={analysisData.tech_and_trends} />}
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