import os
import urllib.request
import urllib.error
import urllib.parse
from typing import Dict

# Define generic webhooks for smart home actions here. 
# You can hook these up to IFTTT, Home Assistant, Node-RED, etc.
WEBHOOKS: Dict[str, str] = {
    "lights_on": os.environ.get("WEBHOOK_LIGHTS_ON", ""),
    "lights_off": os.environ.get("WEBHOOK_LIGHTS_OFF", ""),
    "fan_on": os.environ.get("WEBHOOK_FAN_ON", ""),
    "fan_off": os.environ.get("WEBHOOK_FAN_OFF", "")
}

def trigger_smart_device(action: str) -> str:
    """Sends a stateless HTTP GET request to a smart home webhook."""
    url = WEBHOOKS.get(action)
    if not url:
        return f"No webhook configured for action: {action}. Please set it in backend/actions/smart_home.py or environment variables."
        
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status in [200, 201, 202, 204]:
                return f"Successfully triggered {action.replace('_', ' ')}."
            return f"Smart home hub returned status {response.status}."
    except urllib.error.URLError as e:
        return f"Failed to reach smart home hub: {e.reason}"
    except Exception as e:
        return f"Smart home action failed: {str(e)}"
