import { AlertItem } from '@/types/dashboard';

export const mockAlerts: AlertItem[] = [
  { id: '1', text: "Pressure relief valve PRV-302 inspection overdue", type: "Equipment", severity: "Critical", time: "10 mins ago", status: "New" },
  { id: '2', text: "Procedure for E-105 is not aligned with latest OISD update", type: "Compliance", severity: "High", time: "1 hour ago", status: "New" },
  { id: '3', text: "Vibration analysis recommended for P-301", type: "Predictive", severity: "Medium", time: "2 hours ago", status: "New" },
  { id: '4', text: "New document uploaded: OEM Manual - Turbine T-101", type: "Documents", severity: "Low", time: "3 hours ago", status: "Read" },
  { id: '5', text: "Compliance report is due in 3 days", type: "Compliance", severity: "Medium", time: "4 hours ago", status: "Read" },
];
