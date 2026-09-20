"""
BHU-SYNC Phase H: Security Hardening & Middleware Layer
Provides security headers, input/upload sanitization, bounding-box validation,
rate limiting, and logging hygiene.
"""

import os
import re
import time
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from fastapi import HTTPException, status


# ---------------------------------------------------------------------------
# 1. Security Headers Middleware
# ---------------------------------------------------------------------------

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Applies standard OWASP-recommended security headers to all responses.
    """
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


# ---------------------------------------------------------------------------
# 2. In-Memory Sliding-Window Rate Limiter
# ---------------------------------------------------------------------------

class InMemoryRateLimiter:
    """
    Thread-safe, in-memory sliding window rate limiter for protecting sensitive routes.
    """
    def __init__(self, max_requests: int = 120, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = defaultdict(list)

    def is_allowed(self, client_key: str) -> Tuple[bool, int]:
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean timestamps older than current window
        self.requests[client_key] = [
            ts for ts in self.requests[client_key] if ts > window_start
        ]

        current_count = len(self.requests[client_key])
        if current_count >= self.max_requests:
            remaining_retry = int(self.window_seconds - (now - self.requests[client_key][0]))
            return False, max(1, remaining_retry)

        self.requests[client_key].append(now)
        return True, 0


rate_limiter = InMemoryRateLimiter(max_requests=200, window_seconds=60)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Global rate-limiting middleware for API protection.
    """
    async def dispatch(self, request: Request, call_next):
        # Identify client by forwarded header or client host
        client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
        client_ip = client_ip.split(",")[0].strip()

        # Exempt local testing/internal loops if needed, but enforce rate limiter
        allowed, retry_after = rate_limiter.is_allowed(client_ip)
        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"error": "Too Many Requests", "retry_after_seconds": retry_after},
                headers={"Retry-After": str(retry_after)}
            )

        return await call_next(request)


# ---------------------------------------------------------------------------
# 3. Input & File Upload Validation
# ---------------------------------------------------------------------------

ALLOWED_FILE_EXTENSIONS = {".csv", ".xlsx", ".geojson", ".json"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB limit


def validate_uploaded_file(filename: Optional[str], content: bytes, max_size: int = MAX_FILE_SIZE_BYTES):
    """
    Validates uploaded file against directory traversal, extension whitelist, and size limit.
    Raises HTTPException 400 or 413 on violation.
    """
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File name is required"
        )

    # 1. Path Traversal & dangerous characters check
    if ".." in filename or "/" in filename or "\\" in filename or "\x00" in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file name: directory traversal sequence detected"
        )

    # Strict check on base characters
    if not re.match(r"^[\w\-. ]+$", filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file name: contains disallowed characters"
        )

    # 2. Extension check
    _, ext = os.path.splitext(filename.lower())
    if ext not in ALLOWED_FILE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '{ext}'. Allowed extensions: {', '.join(sorted(ALLOWED_FILE_EXTENSIONS))}"
        )

    # 3. File size check (10MB limit)
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {max_size // (1024*1024)} MB"
        )


def validate_bounding_box(min_lon: float, min_lat: float, max_lon: float, max_lat: float):
    """
    Validates geographic coordinates for spatial queries.
    Longitude: [-180, 180], Latitude: [-90, 90].
    Requires min_lon < max_lon and min_lat < max_lat.
    """
    if not (-180.0 <= min_lon <= 180.0 and -180.0 <= max_lon <= 180.0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Longitude must be between -180 and 180 degrees"
        )

    if not (-90.0 <= min_lat <= 90.0 and -90.0 <= max_lat <= 90.0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Latitude must be between -90 and 90 degrees"
        )

    if min_lon >= max_lon:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid bounding box: min_lon must be strictly less than max_lon"
        )

    if min_lat >= max_lat:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid bounding box: min_lat must be strictly less than max_lat"
        )


def validate_geojson_geometry(geom: dict):
    """
    Validates GeoJSON geometry structure.
    """
    if not isinstance(geom, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Geometry must be a valid GeoJSON object")
    
    geom_type = geom.get("type")
    valid_types = {"Point", "MultiPoint", "LineString", "MultiLineString", "Polygon", "MultiPolygon", "GeometryCollection"}
    if geom_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid GeoJSON geometry type: '{geom_type}'"
        )
    
    coords = geom.get("coordinates")
    if coords is None and geom_type != "GeometryCollection":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing coordinates in geometry")


# ---------------------------------------------------------------------------
# 4. Logging & Secret Hygiene Helpers
# ---------------------------------------------------------------------------

SENSITIVE_KEYS_PATTERN = re.compile(
    r"(authorization|apikey|api_key|secret|password|token|bearer|private_key)",
    re.IGNORECASE
)


def redact_sensitive_dict(data: dict) -> dict:
    """
    Returns a copy of the dictionary with sensitive fields redacted.
    """
    redacted = {}
    for k, v in data.items():
        if SENSITIVE_KEYS_PATTERN.search(str(k)):
            redacted[k] = "[REDACTED]"
        elif isinstance(v, dict):
            redacted[k] = redact_sensitive_dict(v)
        elif isinstance(v, list):
            redacted[k] = [
                redact_sensitive_dict(item) if isinstance(item, dict) else item
                for item in v
            ]
        else:
            redacted[k] = v
    return redacted


def redact_log_string(message: str) -> str:
    """
    Scans a log string for potential Bearer tokens or Supabase service keys and redacts them.
    """
    # Redact Bearer tokens
    message = re.sub(r"Bearer\s+([A-Za-z0-9_\-\.]+)", "Bearer [REDACTED]", message)
    # Redact common API key patterns (e.g. eyJhbGciOi...)
    message = re.sub(r"eyJ[A-Za-z0-9_\-\.]{20,}", "[REDACTED_JWT]", message)
    return message
