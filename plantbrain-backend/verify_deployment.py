"""Verify a deployed PlantBrain backend by exercising core HTTP endpoints."""

from __future__ import annotations

import sys
from typing import Any, Callable

import httpx


DEPLOY_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"


class VerificationSuite:
    """Small synchronous deployment verification suite for Render deployments."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=30.0)
        self.results: list[dict[str, str]] = []
        self.document_id: str = ""

    def check(self, name: str, func: Callable[[], Any]) -> bool:
        """Run one check, record the result, and print a compact status line."""

        try:
            result = func()
            self.results.append({"name": name, "status": "PASS", "detail": str(result)[:100]})
            print(f"  [PASS] {name}")
            return True
        except Exception as exc:
            self.results.append({"name": name, "status": "FAIL", "detail": str(exc)[:200]})
            print(f"  [FAIL] {name}: {str(exc)[:100]}")
            return False

    def verify(self) -> int:
        """Run all deployment checks and return a process exit code."""

        print(f"Verifying PlantBrain deployment: {self.base_url}\n")

        self._section("1. Basic connectivity")
        self.check("GET /", self._check_root)
        self.check("GET /api/v1/health", self._check_health)
        self.check("GET /api/v1/health/deep", self._check_deep_health)

        self._section("2. OpenAPI docs")
        self.check("GET /docs", lambda: self._expect_status("GET", "/docs", 200))
        self.check("GET /openapi.json", self._check_openapi)

        self._section("3. Document ingestion")
        self.check("GET /api/v1/ingest/stats", lambda: self._expect_status("GET", "/api/v1/ingest/stats", 200))
        self.check("GET /api/v1/ingest/list", lambda: self._expect_status("GET", "/api/v1/ingest/list", 200))
        self.check("POST /api/v1/ingest/upload", self._check_upload_document)
        self.check("GET /api/v1/ingest/status/{document_id}", self._check_document_status)

        self._section("4. Query")
        self.check("GET /api/v1/query/history", lambda: self._expect_status("GET", "/api/v1/query/history", 200))
        self.check(
            "GET /api/v1/query/search-chunks?query=test",
            lambda: self._expect_status("GET", "/api/v1/query/search-chunks?query=test", 200),
        )

        self._section("5. Graph")
        self.check("GET /api/v1/graph/stats", lambda: self._expect_status("GET", "/api/v1/graph/stats", 200))
        self.check("GET /api/v1/graph/equipment", lambda: self._expect_status("GET", "/api/v1/graph/equipment", 200))

        self._section("6. Compliance")
        self.check("GET /api/v1/compliance/rules", lambda: self._expect_status("GET", "/api/v1/compliance/rules", 200))
        self.check("POST /api/v1/compliance/seed-rules", lambda: self._expect_status("POST", "/api/v1/compliance/seed-rules", 200))
        self.check("GET /api/v1/compliance/rules non-empty", self._check_compliance_rules_non_empty)

        self._section("7. Patterns")
        self.check("GET /api/v1/patterns/overdue", lambda: self._expect_status("GET", "/api/v1/patterns/overdue", 200))
        self.check("POST /api/v1/patterns/inspections/seed", lambda: self._expect_status("POST", "/api/v1/patterns/inspections/seed", 200))

        self._section("8. Voice")
        self.check("POST /api/v1/voice/transcribe-text", self._check_voice_text_capture)

        self._section("9. WhatsApp webhook")
        self.check("GET /api/v1/whatsapp/webhook", lambda: self._expect_status("GET", "/api/v1/whatsapp/webhook", 200))

        self._section("10. Admin")
        self.check("GET /api/v1/admin/stats", self._check_admin_stats)

        return self._print_summary()

    def close(self) -> None:
        """Close the underlying HTTP client."""

        self.client.close()

    def _section(self, title: str) -> None:
        """Print a section heading."""

        print(f"\n{title}")

    def _url(self, path: str) -> str:
        """Build an absolute URL from an API path."""

        return f"{self.base_url}{path}"

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        """Issue an HTTP request."""

        return self.client.request(method, self._url(path), **kwargs)

    def _expect_status(self, method: str, path: str, expected_status: int) -> dict:
        """Assert that an endpoint returns one exact status code."""

        response = self._request(method, path)
        self._assert_status(response, expected_status)
        return self._safe_json(response)

    def _assert_status(self, response: httpx.Response, expected: int | tuple[int, ...]) -> None:
        """Raise if a response status does not match expected values."""

        expected_values = expected if isinstance(expected, tuple) else (expected,)
        if response.status_code not in expected_values:
            detail = response.text[:300].replace("\n", " ")
            raise AssertionError(f"Expected {expected_values}, got {response.status_code}: {detail}")

    @staticmethod
    def _safe_json(response: httpx.Response) -> dict:
        """Return JSON object or a small text payload fallback."""

        try:
            data = response.json()
            if isinstance(data, dict):
                return data
            return {"data": data}
        except ValueError:
            return {"text": response.text[:120]}

    def _check_root(self) -> dict:
        response = self._request("GET", "/")
        self._assert_status(response, 200)
        return self._safe_json(response)

    def _check_health(self) -> dict:
        response = self._request("GET", "/api/v1/health")
        self._assert_status(response, 200)
        data = self._safe_json(response)
        if data.get("status") != "healthy":
            raise AssertionError(f"Expected status=healthy, got {data}")
        return data

    def _check_deep_health(self) -> dict:
        response = self._request("GET", "/api/v1/health/deep")
        self._assert_status(response, (200, 207))
        return self._safe_json(response)

    def _check_openapi(self) -> dict:
        response = self._request("GET", "/openapi.json")
        self._assert_status(response, 200)
        data = self._safe_json(response)
        if "paths" not in data:
            raise AssertionError("OpenAPI response missing paths key")
        return {"paths": len(data.get("paths", {}))}

    def _check_upload_document(self) -> dict:
        response = self.client.post(
            self._url("/api/v1/ingest/upload"),
            files={"file": ("test.txt", b"Test document", "text/plain")},
            data={"description": "Deployment verification upload"},
        )
        self._assert_status(response, 202)
        data = self._safe_json(response)
        document_id = data.get("document_id")
        if not document_id:
            raise AssertionError(f"Upload response missing document_id: {data}")
        self.document_id = str(document_id)
        return {"document_id": self.document_id}

    def _check_document_status(self) -> dict:
        if not self.document_id:
            raise AssertionError("No document_id available from upload check")
        response = self._request("GET", f"/api/v1/ingest/status/{self.document_id}")
        self._assert_status(response, 200)
        return self._safe_json(response)

    def _check_compliance_rules_non_empty(self) -> dict:
        response = self._request("GET", "/api/v1/compliance/rules")
        self._assert_status(response, 200)
        data = self._safe_json(response)
        total = int(data.get("total", 0))
        rules = data.get("rules", [])
        if total <= 0 and not rules:
            raise AssertionError("Compliance rules are empty after seed")
        return {"total": total or len(rules)}

    def _check_voice_text_capture(self) -> dict:
        response = self.client.post(
            self._url("/api/v1/voice/transcribe-text"),
            json={
                "text": "Pump P-202 is vibrating",
                "equipment_tag": "P-202",
                "severity": "minor",
                "inspector_name": "Test",
            },
        )
        self._assert_status(response, 200)
        return self._safe_json(response)

    def _check_admin_stats(self) -> dict:
        response = self.client.get(self._url("/api/v1/admin/stats"), headers={"X-Admin-Key": "changeme"})
        self._assert_status(response, (200, 401))
        return {"status_code": response.status_code, **self._safe_json(response)}

    def _print_summary(self) -> int:
        """Print final result summary and return process exit code."""

        total = len(self.results)
        failed = [result for result in self.results if result["status"] == "FAIL"]
        pass_count = total - len(failed)
        fail_count = len(failed)
        ready_message = "READY FOR DEMO" if fail_count == 0 else "ISSUES FOUND"

        print("\n===========================================")
        print("DEPLOYMENT VERIFICATION COMPLETE")
        print(f"URL: {self.base_url}")
        print("===========================================")
        print(f"Passed: {pass_count}/{total}")
        print(f"Failed: {fail_count}/{total}")

        if failed:
            print("\nFailed checks:")
            for result in failed:
                print(f"- {result['name']}: {result['detail']}")

        print("\n===========================================")
        print(f"STATUS: {ready_message}")
        print("===========================================")
        return 0 if fail_count == 0 else 1


def main() -> int:
    """Run deployment verification from the command line."""

    suite = VerificationSuite(DEPLOY_URL)
    try:
        return suite.verify()
    finally:
        suite.close()


if __name__ == "__main__":
    raise SystemExit(main())
