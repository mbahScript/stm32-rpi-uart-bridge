import os
import requests
from typing import Dict, Any, List, Optional

BASE_URL = "https://api.tfl.gov.uk"

def _get_key_params() -> Dict[str, str]:
    # TfL currently recommends app_key query parameter
    app_key = os.getenv("TFL_APP_KEY", "").strip()
    return {"app_key": app_key} if app_key else {}

def get_tube_status() -> List[Dict[str, Any]]:
    """
    GET /Line/Mode/tube/Status
    Returns list of line status objects.
    """
    url = f"{BASE_URL}/Line/Mode/tube/Status"
    r = requests.get(url, params=_get_key_params(), timeout=10)
    r.raise_for_status()
    return r.json()

def get_stoppoint_arrivals(stoppoint_id: str) -> List[Dict[str, Any]]:
    """
    GET /StopPoint/{id}/Arrivals
    Works for INDIVIDUAL stop IDs (not groups).
    """
    url = f"{BASE_URL}/StopPoint/{stoppoint_id}/Arrivals"
    r = requests.get(url, params=_get_key_params(), timeout=10)
    r.raise_for_status()
    return r.json()