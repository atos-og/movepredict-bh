import logging
from collections import Counter
from threading import Lock

logger = logging.getLogger("movepredict.api")
_lock = Lock()
_requests: Counter[tuple[str, str, int]] = Counter()


def record_request(method: str, path: str, status_code: int) -> None:
    with _lock:
        _requests[(method, path, status_code)] += 1


def prometheus_metrics() -> str:
    lines = [
        "# HELP movepredict_http_requests_total Total de requisicoes HTTP.",
        "# TYPE movepredict_http_requests_total counter",
    ]
    with _lock:
        items = sorted(_requests.items())
    for (method, path, status), count in items:
        safe_path = path.replace("\\", "\\\\").replace('"', '\\"')
        labels = f'method="{method}",path="{safe_path}",status="{status}"'
        lines.append(f"movepredict_http_requests_total{{{labels}}} {count}")
    return "\n".join(lines) + "\n"
