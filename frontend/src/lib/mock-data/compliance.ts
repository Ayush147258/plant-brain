import { ComplianceRequirement } from '@/types/dashboard';

export const mockCompliance: ComplianceRequirement[] = [
  { id: '1', name: "Pressure Vessel Inspection - Annual", category: "OISD", status: "Compliant", lastCheck: "12 May 2024", nextDue: "12 Nov 2024" },
  { id: '2', name: "Lift Inspection - Periodic", category: "Factory Act", status: "Compliant", lastCheck: "10 May 2024", nextDue: "10 Nov 2024" },
  { id: '3', name: "Electrical Safety Audit", category: "Factory Act", status: "At Risk", lastCheck: "8 May 2024", nextDue: "8 Nov 2024" },
  { id: '4', name: "PESO Licence Renewal", category: "PESO", status: "Compliant", lastCheck: "20 Apr 2024", nextDue: "20 Apr 2025" },
  { id: '5', name: "Fire Safety Equipment Check", category: "Factory Act", status: "Compliant", lastCheck: "15 May 2024", nextDue: "15 Nov 2024" },
  { id: '6', name: "Environment Monitoring Report", category: "Environmental", status: "Compliant", lastCheck: "2 May 2024", nextDue: "2 Nov 2024" },
  { id: '7', name: "Boiler Inspection - Internal", category: "OISD", status: "Non-Compliant", lastCheck: "1 May 2024", nextDue: "-" },
  { id: '8', name: "DG Set Monthly Test", category: "Factory Act", status: "Compliant", lastCheck: "18 Jun 2024", nextDue: "18 Jul 2024" },
];
