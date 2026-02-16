import os

from django.conf import settings
from django.http import JsonResponse


class ApiExceptionToJsonMiddleware:
    """
    Ensure API consumers always receive JSON on unhandled server errors.
    This prevents frontend JSON parse failures when Django would otherwise return HTML.
    """

    API_PREFIXES = (
        "/school/",
        "/testapp/",
        "/nazorat/",
        "/api-token-auth/",
        "/api/",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
        except Exception as exc:  # noqa: BLE001
            if not self._is_api_request(request):
                raise

            debug_errors = settings.DEBUG or os.getenv("API_DEBUG_ERRORS", "false").strip().lower() == "true"
            detail = "Internal server error."
            if debug_errors:
                detail = f"{exc.__class__.__name__}: {exc}"

            return JsonResponse(
                {"detail": detail, "errorType": exc.__class__.__name__},
                status=500,
            )

        if self._is_api_request(request):
            content_type = (response.get("Content-Type") or "").lower()
            if "text/html" in content_type:
                debug_errors = settings.DEBUG or os.getenv("API_DEBUG_ERRORS", "false").strip().lower() == "true"
                detail = (
                    "Backend returned HTML instead of JSON "
                    f"for {request.method} {request.path} (HTTP {response.status_code})."
                )
                if debug_errors:
                    body_preview = ""
                    try:
                        body_preview = (response.content or b"")[:220].decode("utf-8", errors="ignore")
                    except Exception:  # noqa: BLE001
                        body_preview = ""
                    if body_preview:
                        detail = f"{detail} Preview: {body_preview}"

                # If HTML returned with 2xx/3xx on an API route, treat it as server error for API clients.
                status_code = response.status_code if response.status_code >= 400 else 500
                return JsonResponse(
                    {"detail": detail, "errorType": "HtmlErrorResponse"},
                    status=status_code,
                )

        return response

    def _is_api_request(self, request):
        path = request.path or "/"
        if any(path.startswith(prefix) for prefix in self.API_PREFIXES):
            return True

        accept = (request.headers.get("Accept") or "").lower()
        content_type = (request.headers.get("Content-Type") or "").lower()
        return "application/json" in accept or "application/json" in content_type
