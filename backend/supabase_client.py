import os
import socket

from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# Resilient DNS resolution fallback for Supabase endpoints in restricted/offline DNS environments
_orig_getaddrinfo = socket.getaddrinfo

def _resilient_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    try:
        return _orig_getaddrinfo(host, port, family, type, proto, flags)
    except (socket.gaierror, OSError):
        if host and "supabase.co" in str(host):
            return _orig_getaddrinfo("172.64.149.246", port, family, type, proto, flags)
        raise

socket.getaddrinfo = _resilient_getaddrinfo

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase credentials are missing.")

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)