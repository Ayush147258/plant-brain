import { IntegrationItem } from '@/types/dashboard';

export const mockIntegrations: IntegrationItem[] = [
  { id: '1', name: "SAP PM", status: "Connected", lastSync: "5 mins ago", icon: "ti-database", color: "#378add" },
  { id: '2', name: "Maximo", status: "Connected", lastSync: "5 mins ago", icon: "ti-server", color: "#ef9f27" },
  { id: '3', name: "SharePoint", status: "Connected", lastSync: "10 mins ago", icon: "ti-brand-sharepoint", color: "#1d9e75" },
  { id: '4', name: "Email System", status: "Not Connected", lastSync: "-", icon: "ti-mail", color: "#888" },
  { id: '5', name: "WhatsApp Business", status: "Not Connected", lastSync: "-", icon: "ti-brand-whatsapp", color: "#1d9e75" },
  { id: '6', name: "Historians (PI System)", status: "Connected", lastSync: "2 mins ago", icon: "ti-chart-line", color: "#534ab7" },
];
