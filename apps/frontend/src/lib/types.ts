// Local copy of the API contracts. The canonical source is
// packages/shared-types; this keeps the frontend buildable in isolation.

export type SiteStatus =
  | "online"
  | "offline"
  | "degraded"
  | "disabled"
  | "archived"
  | "unknown";

export interface Site {
  id: string;
  slug: string;
  name: string;
  location?: string | null;
  status: SiteStatus;
  nodes_count?: number;
  services_count?: number;
  publications_count?: number;
  peers_count?: number;
  last_seen?: string | null;
}

export interface Service {
  id: string;
  site_id: string;
  name: string;
  slug: string;
  protocol_type: string;
  backend_host: string;
  backend_port: number;
  exposure_mode: string;
  enabled: boolean;
}

export interface Publication {
  id: string;
  service_id: string;
  entrypoint_type: string;
  domain_or_sni?: string | null;
  tls_mode: string;
  public_enabled: boolean;
  maintenance_mode: boolean;
  priority: number;
}

export interface Peer {
  id: string;
  name: string;
  site_id?: string | null;
  assigned_tunnel_ip?: string | null;
  role: string;
  status: string;
  enabled: boolean;
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
