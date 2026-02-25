# Signal Adapters

Polling adapter configurations for the Runtime Anomaly Input Channel (Phase 5).

## Purpose

This directory contains YAML configuration files for polling adapters — components that periodically query external observability APIs for active alerts, anomalies, or signals. Each adapter configuration defines how to connect to an external system and how to map its response fields to the governance runtime signal schema (`governance/schemas/runtime-signal.schema.json`).

Polling adapters are one of four signal ingestion modes defined in the runtime feedback architecture. See `docs/architecture/runtime-feedback.md`, Section 1 (Runtime Anomaly Input Channel) for the full specification.

## Adapter Schema

Each adapter YAML file must contain the following fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `adapter_name` | string | Yes | Unique identifier for this adapter |
| `adapter_version` | string | Yes | Semantic version of this adapter config |
| `source_type` | string | Yes | Always `"polling"` for files in this directory |
| `endpoint` | string | Yes | URL of the external API to poll (supports `${ENV_VAR}` substitution) |
| `auth_method` | string | Yes | Authentication method: `bearer_token`, `basic_auth`, `api_key_header`, `hmac` |
| `auth_secret_ref` | string | Yes | Reference name for the secret in the governance secrets vault |
| `polling_interval_seconds` | integer | Yes | Seconds between polls (minimum: 30) |
| `timeout_seconds` | integer | Yes | Request timeout in seconds |
| `retry_count` | integer | Yes | Number of retries on failure |
| `retry_backoff_base_seconds` | integer | Yes | Base seconds for exponential backoff between retries |
| `signal_mapping` | object | Yes | JSONPath mappings from the API response to runtime signal fields |

### Signal Mapping Fields

The `signal_mapping` object maps external API response fields to the runtime signal schema using JSONPath expressions:

| Mapping Key | Maps To | Description |
|-------------|---------|-------------|
| `severity` | `RuntimeSignal.severity` | Must resolve to: `critical`, `high`, `medium`, `low`, or `informational` |
| `category` | `RuntimeSignal.category` | Must resolve to a valid category enum value |
| `component` | `RuntimeSignal.affected_component` | Service or component identifier |
| `message` | `RuntimeSignal.message` | Human-readable description |
| `timestamp` | `RuntimeSignal.timestamp` | ISO 8601 timestamp of the original signal |

## Usage

1. Copy an example adapter file and modify it for your external system.
2. Store authentication credentials in the governance secrets vault, not in the YAML file.
3. Place the completed adapter file in this directory.
4. The polling adapter runtime reads all `*.yaml` files in this directory on startup.

## Examples

- `example-metrics-api.yaml` — Polling a metrics/alerting API for active alerts
- `example-log-aggregator.yaml` — Polling a log aggregation API for error patterns
- `example-apm-tool.yaml` — Polling an APM/tracing API for performance anomalies
