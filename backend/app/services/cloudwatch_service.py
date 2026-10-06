"""CloudWatchService — metric emission (LLD §16). Logs locally; boto3 in deployed env."""

from __future__ import annotations

from app.config import settings
from app.logging_config import log


class CloudWatchService:
    def __init__(self, namespace: str = "AutoRAG"):
        self.namespace = namespace

    def put_metric(self, name: str, value: float, unit: str = "Count", **dims) -> None:
        dimensions = [{"Name": k, "Value": str(v)} for k, v in dims.items()]
        if settings.ENV == "local":
            log.info("metric", namespace=self.namespace, name=name, value=value, unit=unit, **dims)
            return

        try:
            import boto3

            client = boto3.client("cloudwatch")
            client.put_metric_data(
                Namespace=self.namespace,
                MetricData=[
                    {
                        "MetricName": name,
                        "Value": value,
                        "Unit": unit,
                        "Dimensions": dimensions,
                    }
                ],
            )
        except Exception as exc:  # noqa: BLE001 — never fail the request path on metrics
            log.warning("cloudwatch_put_failed", error=str(exc), name=name, value=value)
