import { EquipmentItem } from '@/types/dashboard';

export const mockEquipment: EquipmentItem[] = [
  { id: "P-201", name: "Pump", type: "Centrifugal Pump", zone: "Zone 3", status: "Active", lastMaintenance: "15 May 2024" },
  { id: "E-105", name: "Heat Exchanger", type: "Shell & Tube", zone: "Zone 2", status: "Active", lastMaintenance: "12 May 2024" },
  { id: "T-101", name: "Turbine", type: "Steam Turbine", zone: "Zone 1", status: "Active", lastMaintenance: "10 May 2024" },
  { id: "V-101", name: "Valve", type: "Control Valve", zone: "Zone 2", status: "Active", lastMaintenance: "8 May 2024" },
  { id: "C-301", name: "Compressor", type: "Air Compressor", zone: "Zone 3", status: "Maintenance", lastMaintenance: "20 May 2024" },
  { id: "P-301", name: "Pump", type: "Centrifugal Pump", zone: "Zone 2", status: "Active", lastMaintenance: "6 May 2024" },
  { id: "E-301", name: "Heat Exchanger", type: "Shell & Tube", zone: "Zone 1", status: "Active", lastMaintenance: "14 May 2024" },
  { id: "V-201", name: "Valve", type: "Gate Valve", zone: "Zone 1", status: "Active", lastMaintenance: "4 May 2024" },
];
