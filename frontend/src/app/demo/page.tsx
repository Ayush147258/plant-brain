import { DemoShell } from '@/components/demo/DemoShell';
import type { PlantRole } from '@/components/demo/RoleSelect';

const validRoles = new Set<PlantRole>(['technician', 'manager', 'head', 'maintenance', 'stores', 'admin']);

export default function DemoPage({ searchParams }: { searchParams?: { role?: string } }) {
  const role = searchParams?.role && validRoles.has(searchParams.role as PlantRole)
    ? (searchParams.role as PlantRole)
    : null;

  return <DemoShell initialRole={role} />;
}