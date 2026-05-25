// Local copy of the API contracts. The canonical source is
// packages/shared-types; this keeps the frontend buildable in isolation.

export type ProtocolType = "http" | "https" | "tcp" | "udp";

export interface WgInfo {
  client_id: string | null;
  name: string | null;
  tunnel_ip: string | null;
  public_key: string | null;
}

export interface PublishedService {
  id: string;
  name: string;
  domain: string | null;
  protocol_type: ProtocolType;
  backend_host: string;
  backend_port: number;
  tls_enabled: boolean;
  proxy_enabled: boolean;
  enabled: boolean;
  publication_id: string | null;
  wg: WgInfo | null;
}

export interface WgClientOption {
  id: string;
  name: string;
  tunnel_ip: string | null;
  enabled: boolean;
}

export interface PublishedServiceCreateResult {
  service: PublishedService;
  wg_config: string | null;
  wg_config_filename: string | null;
}

export interface SettingsInfo {
  project_name?: string;
  environment?: string;
  wgeasy_public_url?: string;
  wgeasy_configured?: boolean;
}
