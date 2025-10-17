from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query
from dotenv import load_dotenv

# Ensure .env is loaded even if this module is imported before main loads it
load_dotenv()

router = APIRouter(prefix="/cluster", tags=["cluster"]) 


def _get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    return os.getenv(key, default)


def _build_client() -> httpx.Client:
    """
    Build an httpx client with optional TLS client certs.
    Falls back to verify=False if CA/certs are not available (for local dev).
    """
    allow_insecure = _get_env("COCKROACH_ALLOW_INSECURE", "true").lower() == "true"
    
    print(f"[DEBUG] Allow insecure: {allow_insecure}")
    
    # If allow_insecure is True, skip all certificate configuration
    if allow_insecure:
        print(f"[DEBUG] Using insecure connection (no certificates, no verification)")
        return httpx.Client(cert=None, verify=False, timeout=30.0)
    
    # Otherwise, configure certificates
    cert_path = _get_env("COCKROACH_CERT", "/root/certs/client.root.crt")
    key_path = _get_env("COCKROACH_KEY", "/root/certs/client.root.key")
    ca_path = _get_env("COCKROACH_CA", "/root/certs/ca.crt")

    print(f"[DEBUG] Cert path: {cert_path} (exists: {os.path.exists(cert_path) if cert_path else False})")
    print(f"[DEBUG] Key path: {key_path} (exists: {os.path.exists(key_path) if key_path else False})")
    print(f"[DEBUG] CA path: {ca_path} (exists: {os.path.exists(ca_path) if ca_path else False})")

    cert_tuple: Optional[tuple[str, str]] = None
    verify: Optional[str | bool] = True

    try:
        if cert_path and key_path and os.path.exists(cert_path) and os.path.exists(key_path):
            cert_tuple = (cert_path, key_path)
            print(f"[DEBUG] Using client certificates")
        if ca_path and os.path.exists(ca_path):
            verify = ca_path
            print(f"[DEBUG] Using CA certificate for verification")
        else:
            verify = False
            print(f"[DEBUG] CA not found, SSL verification disabled")
    except Exception as ex:
        print(f"[DEBUG] Exception in cert setup: {ex}")
        verify = False

    print(f"[DEBUG] Client config - cert_tuple: {bool(cert_tuple)}, verify: {verify}")
    return httpx.Client(cert=cert_tuple, verify=verify, timeout=30.0)


def _session_headers(endpoint_path: str, session_cookie: str) -> Dict[str, str]:
    """
    For `/_status` endpoints we need Cookie: session=...; for /api/v2 use X-Cockroach-API-Session.
    """
    if endpoint_path.startswith("/_status"):
        return {"Cookie": f"session={session_cookie}"}
    return {"X-Cockroach-API-Session": session_cookie}


def _require_settings() -> Dict[str, str]:
    api_url = _get_env("COCKROACHDB_API_URL")
    status_url = _get_env("COCKROACHDB_STATUS_URL")
    session_cookie = _get_env("SESSION_COOKIE")

    if not session_cookie:
        raise HTTPException(status_code=503, detail="SESSION_COOKIE not configured")
    if not api_url:
        raise HTTPException(status_code=503, detail="COCKROACHDB_API_URL not configured")
    if not status_url:
        raise HTTPException(status_code=503, detail="COCKROACHDB_STATUS_URL not configured")

    return {
        "api_url": api_url.rstrip("/"),
        "status_url": status_url,  # full URL to combined statements
        "session_cookie": session_cookie,
    }


# ----------------------------- Helpers to call API -----------------------------

def _fetch_nodes(client: httpx.Client, base_api: str, session_cookie: str) -> List[Dict[str, Any]]:
    endpoint = "/nodes/"
    headers = _session_headers(endpoint, session_cookie)
    url = f"{base_api}{endpoint}"
    print(f"[DEBUG] Fetching nodes from URL: {url}")
    print(f"[DEBUG] Headers: {headers}")
    # Some clusters expect POST, others may allow GET. Try POST first then fallback.
    try:
        print(f"[DEBUG] Attempting POST request...")
        resp = client.post(url, json={}, headers=headers)
        resp.raise_for_status()
        print(f"[DEBUG] POST successful, status: {resp.status_code}")
    except httpx.HTTPStatusError as e:
        print(f"[DEBUG] POST failed with status {e.response.status_code}, trying GET...")
        if e.response.status_code in (404, 405):
            resp = client.get(url, headers=headers)
            resp.raise_for_status()
            print(f"[DEBUG] GET successful, status: {resp.status_code}")
        else:
            raise
    except Exception as e:
        print(f"[DEBUG] Request failed with exception: {type(e).__name__}: {e}")
        raise

    payload = resp.json()
    nodes = payload.get("nodes", [])
    print(f"[DEBUG] Successfully fetched {len(nodes)} nodes")
    return nodes


# --------------------------------- Endpoints ----------------------------------

@router.get("/topology")
def get_cluster_topology() -> List[Dict[str, Any]]:
    """Return node IDs and locality from CockroachDB cluster."""
    settings = _require_settings()
    print(f"[DEBUG] Connecting to API URL: {settings['api_url']}")
    print(f"[DEBUG] Session cookie present: {bool(settings['session_cookie'])}")
    with _build_client() as client:
        try:
            nodes = _fetch_nodes(client, settings["api_url"], settings["session_cookie"])
            return [
                {
                    "node_id": n.get("node_id"),
                    "locality": ", ".join(
                        f"{tier.get('key')}={tier.get('value')}" for tier in (n.get("locality", {}).get("tiers", []) or [])
                    ) or "Unknown",
                }
                for n in nodes
            ]
        except httpx.HTTPError as e:
            print(f"[DEBUG] HTTPError type: {type(e).__name__}")
            print(f"[DEBUG] HTTPError details: {e}")
            if hasattr(e, 'request'):
                print(f"[DEBUG] Request URL: {e.request.url}")
            raise HTTPException(status_code=502, detail=f"Error fetching cluster topology: {e}")


@router.get("/schema/{database}")
def get_database_schema(database: str) -> Dict[str, Any]:
    """Return tables, columns, indexes, and zone config for a database."""
    settings = _require_settings()
    with _build_client() as client:
        try:
            endpoint = f"/databases/{database}/tables/"
            headers = _session_headers(endpoint, settings["session_cookie"])
            tables_resp = client.get(f"{settings['api_url']}{endpoint}", headers=headers)
            tables_resp.raise_for_status()
            table_names: List[str] = tables_resp.json().get("table_names", [])

            result_tables: List[Dict[str, Any]] = []
            for table in table_names:
                det_resp = client.get(
                    f"{settings['api_url']}/databases/{database}/tables/{table}/",
                    headers=headers,
                )
                det_resp.raise_for_status()
                td = det_resp.json()
                result_tables.append(
                    {
                        "name": table,
                        "columns": [
                            {
                                "name": c.get("name"),
                                "type": c.get("type"),
                                "nullable": c.get("nullable"),
                            }
                            for c in (td.get("columns", []) or [])
                        ],
                        "indexes": [
                            {
                                "name": i.get("name"),
                                "unique": i.get("unique"),
                                "columns": i.get("column"),
                            }
                            for i in (td.get("indexes", []) or [])
                        ],
                        "foreign_keys": [fk.get("name") for fk in (td.get("foreign_keys", []) or [])],
                        "zone_config": (
                            {
                                "range_min_bytes": td.get("zone_config", {}).get("range_min_bytes"),
                                "range_max_bytes": td.get("zone_config", {}).get("range_max_bytes"),
                                "gc_ttl_seconds": (td.get("zone_config", {}).get("gc", {}) or {}).get("ttl_seconds"),
                                "num_replicas": td.get("zone_config", {}).get("num_replicas"),
                                "lease_preferences": td.get("zone_config", {}).get("lease_preferences"),
                            }
                            if td.get("zone_config")
                            else None
                        ),
                    }
                )

            return {"database": database, "tables": result_tables}
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Error fetching schema for database {database}: {e}")


@router.get("/cpu-usage")
def get_cpu_usage() -> List[Dict[str, Any]]:
    """Return CPU-related metrics for each node."""
    settings = _require_settings()
    with _build_client() as client:
        try:
            nodes = _fetch_nodes(client, settings["api_url"], settings["session_cookie"])
            return [
                {
                    "node_id": n.get("node_id"),
                    "cpu_usage": (n.get("metrics", {}) or {}).get("sys.cpu.combined.percent-normalized"),
                    "host_cpu_usage": (n.get("metrics", {}) or {}).get("sys.cpu.host.combined.percent-normalized"),
                    "system_cpu_percent": (n.get("metrics", {}) or {}).get("sys.cpu.sys.percent"),
                    "user_cpu_percent": (n.get("metrics", {}) or {}).get("sys.cpu.user.percent"),
                }
                for n in nodes
            ]
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Error fetching CPU usage data: {e}")


@router.get("/slow-statements")
def get_slow_statements(
    app: str = Query("bookly", description="Application name to filter statements by"),
    window_seconds: int = Query(3600, ge=60, le=24 * 3600, description="Lookback window in seconds"),
    limit: int = Query(10, ge=1, le=200, description="Max statements to return"),
) -> List[Dict[str, Any]]:
    """Return slow statements from the admin combined statements endpoint filtered by app."""
    settings = _require_settings()
    now = int(time.time())
    start = now - window_seconds

    # COCKROACHDB_STATUS_URL should point to .../_status/combinedstmts
    base_status_url = settings["status_url"].split("?")[0]
    url = (
        f"{base_status_url}?start={start}&end={now}"
        f"&fetch_mode.stats_type=0&fetch_mode.sort=0&limit={limit}"
    )

    headers = _session_headers("/_status/combinedstmts", settings["session_cookie"])

    with _build_client() as client:
        try:
            resp = client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            statements = data.get("statements", [])
            filtered = [s for s in statements if ((s.get("key", {}).get("keyData", {}) or {}).get("app") == app)]
            result = [
                {
                    "query": (s.get("key", {}).get("keyData", {}) or {}).get("query"),
                    "app": (s.get("key", {}).get("keyData", {}) or {}).get("app") or "Unknown",
                    "mean_latency": (s.get("stats", {}) or {}).get("serviceLat", {}).get("mean"),
                    "rows_read": (s.get("stats", {}) or {}).get("rowsRead", {}).get("mean"),
                    "rows_written": (s.get("stats", {}) or {}).get("rowsWritten", {}).get("mean"),
                    "index_recommendations": (s.get("stats", {}) or {}).get("indexRecommendations") or [],
                }
                for s in filtered
            ]
            return result
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Error fetching slow statements: {e}")


@router.get("/all")
def get_all(
    database: str = Query("bookly", description="Database name for schema fetch"),
    app: str = Query("bookly", description="Application filter for slow statements"),
) -> Dict[str, Any]:
    """Aggregate topology, schema, CPU usage, and slow statements in one call."""
    # Keep simple and sequential for now; can parallelize later with anyio
    try:
        topo = get_cluster_topology()
    except HTTPException:
        topo = []

    try:
        schema = get_database_schema(database)
    except HTTPException:
        schema = {"database": database, "tables": []}

    try:
        cpu = get_cpu_usage()
    except HTTPException:
        cpu = []

    try:
        slow = get_slow_statements(app=app)
    except HTTPException:
        slow = []

    return {"topology": topo, "schema": schema, "cpuUsage": cpu, "slowStatements": slow}
