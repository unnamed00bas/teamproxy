// Shared TypeScript contracts mirroring the backend API.
// Kept hand-written and small; can later be generated from the OpenAPI schema
// served at /api/v1/openapi.json.

export type Role = "superadmin" | "operator" | "viewer";
export type SiteStatus =
  | "online"
  | "offline"
  | "degraded"
  | "disabled"
  | "archived"
  | "unknown";
export type PeerStatus = "active" | "stale" | "disabled" | "unknown";
export type ProtocolType = "http" | "https" | "tcp" | "udp";
export type ExposureMode = "public" | "private" | "disabled";
export type EntrypointType = "web" | "tcp" | "udp";
export type TlsMode = "off" | "letsencrypt" | "passthrough" | "custom";
export type HealthStatus = "green" | "yellow" | "red" | "unknown";

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface Site {
  id: string;
  slug: string;
  name: string;
  description?: string | null;
  location?: string | null;
  status: SiteStatus;
  wg_tunnel_subnet?: string | null;
  local_subnets: string[];
  tags: string[];
  gateway_peer_id?: string | null;
  agent_version?: string | null;
  last_seen?: string | null;
  nodes_count?: number;
  services_count?: number;
  publications_count?: number;
  peers_count?: number;
  created_at: string;
  updated_at: string;
}

export interface Service {
  id: string;
  site_id: string;
  node_id?: string | null;
  name: string;
  slug: string;
  protocol_type: ProtocolType;
  backend_host: string;
  backend_port: number;
  backend_scheme: string;
  exposure_mode: ExposureMode;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface Publication {
  id: string;
  service_id: string;
  entrypoint_type: EntrypointType;
  domain_or_sni?: string | null;
  path_prefix?: string | null;
  tls_enabled: boolean;
  tls_mode: TlsMode;
  published_port?: number | null;
  public_enabled: boolean;
  maintenance_mode: boolean;
  priority: number;
  created_at: string;
  updated_at: string;
}

export interface DashboardStats {
  sites_total: number;
  sites_online: number;
  sites_offline: number;
  peers_total: number;
  peers_active: number;
  services_total: number;
  publications_total: number;
  publications_public: number;
  broken_routes: number;
  expiring_certificates: number;
  recent_audit: AuditEvent[];
  recent_failed_deploys: unknown[];
}

export interface AuditEvent {
  id: string;
  created_at: string;
  actor_email?: string | null;
  action: string;
  target_type?: string | null;
  target_id?: string | null;
  result: string;
}
