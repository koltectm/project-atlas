#!/usr/bin/env python3
"""
Project Atlas — Production Smoke Test Suite
============================================
Run against the live deployed backend to verify all critical paths.

Usage:
  python smoke_test.py --base-url https://your-app.railway.app
  python smoke_test.py --base-url https://your-app.railway.app --email admin@test.com --password secret123

Exit code 0 = all tests pass
Exit code 1 = one or more failures
"""

import argparse
import json
import sys
import time
import uuid
from datetime import datetime
from typing import Optional

try:
    import httpx
except ImportError:
    print("ERROR: httpx required. Install with: pip install httpx")
    sys.exit(1)

# ── Colour output (no external deps) ─────────────────────────────────────────

RESET  = "\033[0m"
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"

def ok(msg):   print(f"  {GREEN}✅ PASS{RESET}  {msg}")
def fail(msg): print(f"  {RED}❌ FAIL{RESET}  {msg}")
def info(msg): print(f"  {CYAN}ℹ  INFO{RESET}  {msg}")
def head(msg): print(f"\n{BOLD}{CYAN}{'═'*60}{RESET}\n{BOLD}{msg}{RESET}")

# ── Test runner ───────────────────────────────────────────────────────────────

class SmokeTest:
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.client   = httpx.Client(timeout=timeout, follow_redirects=True)
        self.token: Optional[str] = None
        self.results  = {"pass": 0, "fail": 0, "errors": []}

        # Test data — unique per run to avoid collisions
        run_id = uuid.uuid4().hex[:8]
        self.test_email    = f"smoketest_{run_id}@atlas-test.invalid"
        self.test_password = "SmokeTest@123"
        self.test_name     = f"Smoke Test User {run_id}"
        self.scenario_id: Optional[str] = None
        self.run_id:      Optional[str] = None

    def _h(self) -> dict:
        """Authenticated headers."""
        h = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def _check(self, name: str, condition: bool, detail: str = ""):
        if condition:
            ok(name)
            self.results["pass"] += 1
        else:
            fail(f"{name}  →  {detail}")
            self.results["fail"] += 1
            self.results["errors"].append(f"{name}: {detail}")

    def _get(self, path: str, **kw):
        return self.client.get(f"{self.base_url}{path}", headers=self._h(), **kw)

    def _post(self, path: str, data: dict = None, **kw):
        return self.client.post(
            f"{self.base_url}{path}", headers=self._h(),
            content=json.dumps(data) if data else None, **kw
        )

    def _delete(self, path: str):
        return self.client.delete(f"{self.base_url}{path}", headers=self._h())

    # ── Tests ─────────────────────────────────────────────────────────────────

    def test_health(self):
        head("1 · Health & Readiness Endpoints")
        try:
            r = self.client.get(f"{self.base_url}/health", timeout=10)
            self._check("GET /health returns 200",           r.status_code == 200, f"got {r.status_code}")
            body = r.json()
            self._check("/health body has status=healthy",   body.get("status") == "healthy", str(body))
        except Exception as e:
            fail(f"GET /health raised exception: {e}")
            self.results["fail"] += 1

        try:
            r = self.client.get(f"{self.base_url}/ready", timeout=15)
            self._check("GET /ready returns 200",            r.status_code == 200, f"got {r.status_code}")
            body = r.json()
            self._check("/ready database=connected",         body.get("database") == "connected", str(body))
        except Exception as e:
            fail(f"GET /ready raised exception: {e}")
            self.results["fail"] += 1

    def test_security_headers(self):
        head("2 · Security Headers")
        try:
            r = self.client.get(f"{self.base_url}/health")
            hdrs = {k.lower(): v for k, v in r.headers.items()}
            # Backend headers (set by Railway/nginx or FastAPI middleware)
            # Frontend headers (set by Vercel) — tested separately
            # For backend we just verify no X-Powered-By leaks
            self._check("No X-Powered-By header leaked",
                "x-powered-by" not in hdrs,
                f"found: {hdrs.get('x-powered-by','')}")
        except Exception as e:
            fail(f"Header check failed: {e}")
            self.results["fail"] += 1

    def test_unauthenticated_rejection(self):
        head("3 · Unauthenticated Access Rejection")
        self.token = None   # ensure no token
        try:
            r = self._get("/api/v1/nodes")
            self._check("GET /api/v1/nodes without token → 401",
                r.status_code == 401, f"got {r.status_code}")
            r2 = self._post("/api/v1/simulations/run", {"scenario_id": str(uuid.uuid4())})
            self._check("POST /api/v1/simulations/run without token → 401",
                r2.status_code == 401, f"got {r2.status_code}")
        except Exception as e:
            fail(f"Auth rejection test failed: {e}")
            self.results["fail"] += 1

    def test_docs_disabled(self):
        head("4 · OpenAPI Docs Disabled in Production")
        try:
            r = self.client.get(f"{self.base_url}/docs",   follow_redirects=False)
            self._check("GET /docs returns 404 in production",
                r.status_code == 404, f"got {r.status_code}")
            r2 = self.client.get(f"{self.base_url}/redoc", follow_redirects=False)
            self._check("GET /redoc returns 404 in production",
                r2.status_code == 404, f"got {r2.status_code}")
        except Exception as e:
            info(f"Docs check skipped (may be dev environment): {e}")

    def test_register(self):
        head("5 · Authentication — Register")
        try:
            from supabase import create_client  # optional; skip if not installed
            info("Supabase SDK available — registration may need Supabase credentials")
        except ImportError:
            pass

        try:
            r = self._post("/api/v1/auth/register", {
                "email": self.test_email,
                "password": self.test_password,
                "full_name": self.test_name,
                "organization": "Atlas Smoke Test",
            })
            self._check("POST /api/v1/auth/register returns 201 or 200",
                r.status_code in (200, 201), f"got {r.status_code}: {r.text[:200]}")
        except Exception as e:
            info(f"Register endpoint error (may need Supabase): {e}")

    def test_login(self, email: str = None, password: str = None):
        head("6 · Authentication — Login")
        email    = email    or self.test_email
        password = password or self.test_password
        try:
            r = self._post("/api/v1/auth/login", {"email": email, "password": password})
            self._check("POST /api/v1/auth/login returns 200",
                r.status_code == 200, f"got {r.status_code}: {r.text[:200]}")
            if r.status_code == 200:
                body = r.json()
                token = (body.get("access_token") or
                         body.get("data", {}).get("access_token") if isinstance(body.get("data"), dict) else None)
                self._check("Login response contains access_token",
                    bool(token), f"body keys: {list(body.keys())}")
                if token:
                    self.token = token
                    ok(f"Token stored (prefix: {token[:20]}…)")
        except Exception as e:
            fail(f"Login failed: {e}")
            self.results["fail"] += 1

    def test_me(self):
        head("7 · Authenticated User Profile")
        try:
            r = self._get("/api/v1/auth/me")
            self._check("GET /api/v1/auth/me returns 200",
                r.status_code == 200, f"got {r.status_code}: {r.text[:200]}")
            if r.status_code == 200:
                body = r.json()
                data = body.get("data", body)
                self._check("Profile has email field",  "email" in data or "email" in body, str(data)[:100])
                self._check("Profile has role field",   "role"  in data or "role"  in body, str(data)[:100])
        except Exception as e:
            fail(f"Profile fetch failed: {e}")
            self.results["fail"] += 1

    def test_nodes(self):
        head("8 · Supply Chain Nodes")
        try:
            r = self._get("/api/v1/nodes")
            self._check("GET /api/v1/nodes returns 200",
                r.status_code == 200, f"got {r.status_code}")
            if r.status_code == 200:
                body = r.json()
                items = body.get("items") or body.get("data", {}).get("items") or body
                if isinstance(items, list):
                    self._check(f"Nodes list has ≥40 items",
                        len(items) >= 40, f"got {len(items)}")
                else:
                    info(f"Nodes response shape: {list(body.keys())}")

            r2 = self._get("/api/v1/nodes/graph")
            self._check("GET /api/v1/nodes/graph returns 200",
                r2.status_code == 200, f"got {r2.status_code}")
            if r2.status_code == 200:
                body2 = r2.json()
                data  = body2.get("data", body2)
                self._check("Graph response has nodes key",  "nodes" in data, str(list(data.keys()))[:100])
                self._check("Graph response has edges key",  "edges" in data, str(list(data.keys()))[:100])
                if "nodes" in data:
                    self._check(f"Graph has ≥40 nodes", len(data["nodes"]) >= 40, f"got {len(data['nodes'])}")
        except Exception as e:
            fail(f"Nodes test failed: {e}")
            self.results["fail"] += 1

    def test_disruption_types(self):
        head("9 · Disruption Types")
        try:
            r = self._get("/api/v1/disruptions")
            self._check("GET /api/v1/disruptions returns 200",
                r.status_code == 200, f"got {r.status_code}")
            if r.status_code == 200:
                body  = r.json()
                items = body.get("items") or body.get("data", {}).get("items") or body
                if isinstance(items, list):
                    self._check("≥25 disruption types exist",
                        len(items) >= 25, f"got {len(items)}")
        except Exception as e:
            fail(f"Disruptions test failed: {e}")
            self.results["fail"] += 1

    def test_scenario_crud(self):
        head("10 · Scenario CRUD")
        try:
            # Create
            payload = {
                "scenario_name":         f"Smoke Test Scenario {uuid.uuid4().hex[:6]}",
                "description":           "Automated smoke test scenario — safe to delete",
                "time_horizon_days":     90,
                "simulation_iterations": 1000,
                "is_public":             False,
                "tags":                  ["smoke-test"],
                "disruptions":           [],
            }
            r = self._post("/api/v1/scenarios", payload)
            self._check("POST /api/v1/scenarios returns 200 or 201",
                r.status_code in (200, 201), f"got {r.status_code}: {r.text[:200]}")

            if r.status_code in (200, 201):
                body = r.json()
                data = body.get("data", body)
                sid  = data.get("scenario_id")
                self._check("Create response has scenario_id", bool(sid), str(data)[:100])
                if sid:
                    self.scenario_id = str(sid)

            # Read
            if self.scenario_id:
                r2 = self._get(f"/api/v1/scenarios/{self.scenario_id}")
                self._check(f"GET /api/v1/scenarios/{{id}} returns 200",
                    r2.status_code == 200, f"got {r2.status_code}")

            # List mine
            r3 = self._get("/api/v1/scenarios/mine")
            self._check("GET /api/v1/scenarios/mine returns 200",
                r3.status_code == 200, f"got {r3.status_code}")

        except Exception as e:
            fail(f"Scenario CRUD failed: {e}")
            self.results["fail"] += 1

    def test_simulation(self):
        head("11 · Simulation Trigger & Polling")
        if not self.scenario_id:
            info("Skipping — no scenario created (previous test failed)")
            return
        try:
            # Trigger
            r = self._post("/api/v1/simulations/run", {"scenario_id": self.scenario_id})
            self._check("POST /api/v1/simulations/run returns 200 or 202",
                r.status_code in (200, 201, 202), f"got {r.status_code}: {r.text[:300]}")

            if r.status_code in (200, 201, 202):
                body    = r.json()
                data    = body.get("data", body)
                run_id  = data.get("run_id")
                self._check("Run response has run_id", bool(run_id), str(data)[:100])

                if run_id:
                    self.run_id = str(run_id)
                    info(f"Run ID: {self.run_id}")

                    # Poll for completion (max 120s for 1000 iterations)
                    deadline = time.time() + 120
                    status   = "queued"
                    while time.time() < deadline and status in ("queued", "running"):
                        time.sleep(3)
                        r2 = self._get(f"/api/v1/simulations/{self.run_id}")
                        if r2.status_code == 200:
                            body2  = r2.json()
                            data2  = body2.get("data", body2)
                            status = data2.get("status", "unknown")
                            pct    = data2.get("completed_iterations", 0)
                            total  = data2.get("total_iterations", 1000)
                            info(f"  Status: {status}  ({pct}/{total})")
                        else:
                            break

                    self._check(f"Simulation completed (status={status})",
                        status == "completed", f"final status: {status}")
        except Exception as e:
            fail(f"Simulation test failed: {e}")
            self.results["fail"] += 1

    def test_results(self):
        head("12 · Results Retrieval")
        if not self.run_id:
            info("Skipping — no completed run available")
            return
        try:
            r = self._get(f"/api/v1/results/{self.run_id}/aggregates")
            self._check("GET /results/{run_id}/aggregates returns 200",
                r.status_code == 200, f"got {r.status_code}")
            if r.status_code == 200:
                body = r.json()
                data = body.get("data", body)
                aggs = data if isinstance(data, list) else data.get("items", [])
                self._check("Aggregates list is non-empty", len(aggs) > 0, f"got {len(aggs)}")

            r2 = self._get(f"/api/v1/results/{self.run_id}/vulnerability")
            self._check("GET /results/{run_id}/vulnerability returns 200",
                r2.status_code == 200, f"got {r2.status_code}")

            r3 = self._get(f"/api/v1/results/{self.run_id}/iterations", params={"limit": 10, "offset": 0})
            self._check("GET /results/{run_id}/iterations returns 200",
                r3.status_code == 200, f"got {r3.status_code}")
        except Exception as e:
            fail(f"Results test failed: {e}")
            self.results["fail"] += 1

    def test_viewer_role_blocked(self):
        head("13 · Role Enforcement (Viewer Cannot Run Simulations)")
        # This test is advisory — requires a separate viewer-role account
        info("Role test requires a viewer-role account — verify manually via E2E-041")

    def test_rate_limit(self):
        head("14 · Rate Limit Enforcement")
        try:
            # Send 65 rapid requests to trigger the 60/min limit
            hit_429 = False
            for i in range(65):
                r = self.client.get(f"{self.base_url}/api/v1/nodes", headers=self._h())
                if r.status_code == 429:
                    hit_429 = True
                    info(f"Rate limit hit at request #{i+1}")
                    break
            self._check("Rate limit triggers 429 after burst",
                hit_429, "60 requests sent — no 429 received (rate limiter may not be active)")
        except Exception as e:
            info(f"Rate limit test inconclusive: {e}")

    def test_sql_injection(self):
        head("15 · Security — SQL Injection Rejection")
        try:
            r = self._get("/api/v1/nodes", params={"stage": "upstream'; DROP TABLE supply_chain_nodes; --"})
            self._check("SQL injection string → 422 (Pydantic rejects invalid ENUM)",
                r.status_code == 422, f"got {r.status_code}: {r.text[:100]}")
        except Exception as e:
            fail(f"SQL injection test failed: {e}")
            self.results["fail"] += 1

    def test_path_traversal(self):
        head("16 · Security — Path Traversal Rejection")
        try:
            r = self._get("/api/v1/nodes/../../etc/passwd")
            self._check("Path traversal → 422 or 404 (UUID validation rejects)",
                r.status_code in (404, 422), f"got {r.status_code}")
        except Exception as e:
            fail(f"Path traversal test failed: {e}")
            self.results["fail"] += 1

    def test_mass_assignment(self):
        head("17 · Security — Mass Assignment Rejection")
        if not self.token:
            info("Skipping — not authenticated")
            return
        try:
            r = self._post("/api/v1/scenarios", {
                "scenario_name":         "Mass Assignment Test",
                "time_horizon_days":     30,
                "simulation_iterations": 100,
                "is_public":             False,
                "disruptions":           [],
                "role":                  "admin",       # should be ignored
                "is_superuser":          True,          # should be ignored
                "created_by":            "00000000-0000-0000-0000-000000000000",  # should be ignored
            })
            self._check("Extra fields accepted without error (Pydantic ignores them)",
                r.status_code in (200, 201), f"got {r.status_code}: {r.text[:200]}")
            if r.status_code in (200, 201):
                body = r.json()
                data = body.get("data", body)
                self._check("Response does not contain role=admin",
                    data.get("role") != "admin", f"role in response: {data.get('role')}")
        except Exception as e:
            fail(f"Mass assignment test failed: {e}")
            self.results["fail"] += 1

    def cleanup(self):
        head("18 · Cleanup — Delete Test Data")
        if self.scenario_id and self.token:
            try:
                r = self._delete(f"/api/v1/scenarios/{self.scenario_id}")
                if r.status_code in (200, 204):
                    ok(f"Test scenario {self.scenario_id} deleted")
                else:
                    info(f"Could not delete test scenario: {r.status_code}")
            except Exception:
                pass

    def run_all(self, login_email: str = None, login_password: str = None):
        print(f"\n{BOLD}{CYAN}{'╔' + '═'*58 + '╗'}{RESET}")
        print(f"{BOLD}{CYAN}║  PROJECT ATLAS — PRODUCTION SMOKE TEST SUITE{' '*12}║{RESET}")
        print(f"{BOLD}{CYAN}║  Target: {self.base_url:<48}║{RESET}")
        print(f"{BOLD}{CYAN}║  Time:   {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'):<48}║{RESET}")
        print(f"{BOLD}{CYAN}{'╚' + '═'*58 + '╝'}{RESET}\n")

        self.test_health()
        self.test_security_headers()
        self.test_unauthenticated_rejection()
        self.test_docs_disabled()
        if login_email and login_password:
            # Skip registration if credentials provided — use existing account
            self.test_login(login_email, login_password)
        else:
            self.test_register()
            self.test_login()
        self.test_me()
        self.test_nodes()
        self.test_disruption_types()
        self.test_scenario_crud()
        self.test_simulation()
        self.test_results()
        self.test_viewer_role_blocked()
        self.test_rate_limit()
        self.test_sql_injection()
        self.test_path_traversal()
        self.test_mass_assignment()
        self.cleanup()

        # ── Final report ──────────────────────────────────────────────────────
        total = self.results["pass"] + self.results["fail"]
        print(f"\n{BOLD}{'═'*60}{RESET}")
        print(f"{BOLD}RESULTS: {self.results['pass']}/{total} tests passed{RESET}")
        if self.results["errors"]:
            print(f"\n{RED}FAILURES:{RESET}")
            for e in self.results["errors"]:
                print(f"  • {e}")
        print(f"{'═'*60}\n")
        return self.results["fail"] == 0


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Project Atlas Production Smoke Test")
    parser.add_argument("--base-url",  required=True, help="Backend base URL (no trailing slash)")
    parser.add_argument("--email",     default=None,  help="Existing user email (skips registration)")
    parser.add_argument("--password",  default=None,  help="Existing user password")
    parser.add_argument("--timeout",   type=int, default=30, help="HTTP timeout seconds (default 30)")
    args = parser.parse_args()

    runner = SmokeTest(args.base_url, timeout=args.timeout)
    success = runner.run_all(args.email, args.password)
    sys.exit(0 if success else 1)
