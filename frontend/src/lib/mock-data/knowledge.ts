import { KnowledgeItem } from '@/types/dashboard';

export const mockKnowledge: KnowledgeItem[] = [
  { id: '1', title: "P-201 Pump Seal Replacement Best Practice", type: "Voice", expert: "Rajesh Kumar", capturedOn: "28 May 2024", status: "Documented" },
  { id: '2', title: "V-101 Valve Troubleshooting Guide", type: "Voice", expert: "Suresh Patel", capturedOn: "18 May 2024", status: "Documented" },
  { id: '3', title: "E-105 Heat Exchanger Cleaning Procedure", type: "Document", expert: "Amit Singh", capturedOn: "18 May 2024", status: "Documented" },
  { id: '4', title: "T-101 Turbine Start-up Checklist", type: "Voice", expert: "Vikram Joshi", capturedOn: "17 May 2024", status: "Pending Review" },
  { id: '5', title: "C-301 Compressor Maintenance Tips", type: "Voice", expert: "Rajesh Kumar", capturedOn: "16 May 2024", status: "Documented" },
];
