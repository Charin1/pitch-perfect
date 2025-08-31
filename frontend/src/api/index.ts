// From: frontend/src/api/index.ts
// ----------------------------------------
import axios from "axios";

// Ensure this points to your backend. The default is http://127.0.0.1:8000
const api = axios.create({ 
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000" 
});

// --- Interfaces for TypeScript ---
export interface Lead {
  id: number;
  company_name: string;
  website_url: string;
  status: 'PENDING' | 'CRAWLING' | 'ANALYZING' | 'COMPLETED' | 'FAILED';
  page_title?: string;
  summary?: string;
  bullet_points?: string;
  analysis_json?: string;
  created_at: string;
}


export interface Pitch {
  id: number;
  lead_id: number;
  content: string;
  created_at: string;
}

// --- LEADS API Calls ---
export const getLeads = (): Promise<Lead[]> => 
  api.get("/api/v1/leads/").then(res => res.data);

export const createLead = (data: { company_name: string; website_url: string }): Promise<Lead> =>
  api.post("/api/v1/leads/", data).then(res => res.data);

export const getLeadDetails = (leadId: number): Promise<Lead> =>
  api.get(`/api/v1/leads/${leadId}`).then(res => res.data);

export const deleteLead = (leadId: number): Promise<void> => 
  api.delete(`/api/v1/leads/${leadId}`);

// --- PITCHES API Calls ---

// --- THIS IS THE CORRECTED FUNCTION ---
export const generatePitch = (leadId: number, user_product: string): Promise<Pitch> =>
  // It now correctly calls the new, more RESTful endpoint
  api.post(`/api/v1/leads/${leadId}/generate-pitch`, { 
    // The lead_id is in the URL, so the body only needs the description
    user_product_description: user_product 
  }).then(res => res.data);