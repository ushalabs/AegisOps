import httpx

from app.core.config import settings


class PrometheusError(Exception):
    pass


class PrometheusClient:
    def __init__(self):
        self.base_url = settings.prometheus_url.rstrip("/")

    def query(self, promql: str) -> list[dict]:
        try:
            response = httpx.get(
                f"{self.base_url}/api/v1/query",
                params={"query": promql},
                timeout=5.0,
            )

            response.raise_for_status()

        except httpx.HTTPError as exc:
            raise PrometheusError(
                f"Failed to query Prometheus: {exc}"
            ) from exc

        payload = response.json()

        if payload.get("status") != "success":
            raise PrometheusError(
                "Prometheus returned an unsuccessful response"
            )

        return payload["data"]["result"]


prometheus_client = PrometheusClient()