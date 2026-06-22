export interface DocumentItem {
  id: string;
  name: string;
  category: string;
  type: string;
  uploadDate: string;
  size: string;
}

export interface EquipmentItem {
  id: string;
  name: string;
  type: string;
  zone: string;
  status: 'Active' | 'Maintenance' | 'Offline';
  lastMaintenance: string;
}

export interface WorkOrder {
  id: string;
  title: string;
  type: string;
  priority: 'High' | 'Medium' | 'Low';
  status: 'Open' | 'In Progress' | 'Pending' | 'Closed';
  assignedTo: string;
  dueDate: string;
}

export interface ComplianceRequirement {
  id: string;
  name: string;
  category: string;
  status: 'Compliant' | 'At Risk' | 'Non-Compliant';
  lastCheck: string;
  nextDue: string;
}

export interface KnowledgeItem {
  id: string;
  title: string;
  type: 'Voice' | 'Document';
  expert: string;
  capturedOn: string;
  status: 'Documented' | 'Pending Review';
}

export interface AlertItem {
  id: string;
  text: string;
  type: string;
  severity: 'Critical' | 'High' | 'Medium' | 'Low';
  time: string;
  status: 'New' | 'Read';
}

export interface IntegrationItem {
  id: string;
  name: string;
  status: 'Connected' | 'Not Connected';
  lastSync: string;
  icon: string;
  color: string;
}
