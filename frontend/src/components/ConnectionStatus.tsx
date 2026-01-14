import type { ConnectionStatus as Status } from '../types/poker';

interface ConnectionStatusProps {
  status: Status;
}

const statusConfig: Record<Status, { label: string; color: string; bgColor: string }> = {
  disconnected: {
    label: 'Disconnected',
    color: 'text-gray-400',
    bgColor: 'bg-gray-600',
  },
  connecting: {
    label: 'Connecting...',
    color: 'text-amber-400',
    bgColor: 'bg-amber-500',
  },
  connected: {
    label: 'Connected',
    color: 'text-poker-green-400',
    bgColor: 'bg-poker-green-500',
  },
  error: {
    label: 'Error',
    color: 'text-red-400',
    bgColor: 'bg-red-500',
  },
};

export function ConnectionStatus({ status }: ConnectionStatusProps) {
  const config = statusConfig[status];

  return (
    <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full bg-gray-800/50 ${config.color}`}>
      <div className={`w-2 h-2 rounded-full ${config.bgColor} ${status === 'connecting' ? 'animate-pulse' : ''}`} />
      <span className="text-sm font-medium">{config.label}</span>
    </div>
  );
}
