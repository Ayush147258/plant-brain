import { WorkOrder } from '@/types/dashboard';

export const mockWorkOrders: WorkOrder[] = [
  { id: "WO-2024-324", title: "P-201 Pump Seal Replacement", type: "Maintenance", priority: "High", status: "Open", assignedTo: "Rajesh Kumar", dueDate: "24 May 2024" },
  { id: "WO-2024-323", title: "E-105 Tube Cleaning", type: "Maintenance", priority: "Medium", status: "In Progress", assignedTo: "Suresh Patel", dueDate: "25 May 2024" },
  { id: "WO-2024-322", title: "V-101 Valve Calibration", type: "Inspection", priority: "Medium", status: "In Progress", assignedTo: "Amit Singh", dueDate: "22 May 2024" },
  { id: "WO-2024-321", title: "C-301 Compressor Check", type: "Maintenance", priority: "High", status: "Pending", assignedTo: "Vikram Joshi", dueDate: "21 May 2024" },
  { id: "WO-2024-320", title: "T-101 Turbine Inspection", type: "Inspection", priority: "Low", status: "Open", assignedTo: "Rajesh Kumar", dueDate: "24 May 2024" },
  { id: "WO-2024-319", title: "P-301 Pump Bearing Change", type: "Maintenance", priority: "High", status: "In Progress", assignedTo: "Suresh Patel", dueDate: "28 May 2024" },
  { id: "WO-2024-318", title: "E-301 Leak Inspection", type: "Inspection", priority: "Low", status: "Closed", assignedTo: "Amit Singh", dueDate: "19 May 2024" },
];
