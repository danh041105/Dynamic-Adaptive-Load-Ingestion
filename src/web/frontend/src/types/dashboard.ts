export type RequestStatus = 'PENDING' | 'SCHEDULED' | 'RECEIVED' | 'PROCESSING' | 'RUNNING' | 'DOWNLOADING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';

export type SourceStatus = 'Available' | 'Busy' | 'Offline' | 'Maintenance' | 'UNAVAILABLE' | 'AVAILABLE';

export type SystemLoadLevel = 'Low' | 'Moderate' | 'High' | 'Critical';

export interface AuthUser {
  user_id: number;
  username: string;
  role: string;
}

export interface EnmSource {
  id: string;
  rawId?: number;
  name: string;
  vendor: string;
  region: string;
  ipAddress: string;
  status: SourceStatus;
  activeTasks: number;
  maxTasks: number;
  latencyMs: number;
  lastSync: string;
}

export interface DownloadRequest {
  id: string; // e.g. "#1", "#2"
  rawId?: number;
  sourceId: string; // e.g. "GEO|ListFile|HN" or "ENM01"
  rawSourceId?: number;
  timeWindow: {
    start: string; // "10:00"
    end: string;   // "12:00"
    date?: string;
  };
  status: RequestStatus;
  progress: number; // 0 - 100
  fileCount?: number;
  totalSizeMb?: number;
  downloadSpeed?: string;
  dataType?: 'Cell Trace' | 'PM Counters' | 'Alarm Logs' | 'Raw PCAP';
  priority?: 'Low' | 'Normal' | 'High' | 'Urgent';
  createdAt: string;
  eta?: string;
  failureReason?: string;
}

export interface SystemMetrics {
  activeSources: number;
  totalSources: number;
  queueFiles: number;
  queueUnit: string;
  loadLevel: SystemLoadLevel;
  cpuUsagePct: number;
  memoryUsagePct: number;
  throughputRate: string;
  totalRequests?: number;
}
