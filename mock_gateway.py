"""A miniature stand-in for an AI router/gateway with three mock providers,
modeled on the three failure modes Dragos and OpenRouter both documented
this week: a clean provider, one that retains despite a ZDR flag, and one
that forwards to an undisclosed second hop.

Nothing here talks to a real AI provider. "Touching the canary" is how a
mock provider stands in for logging or forwarding a prompt it was told not
to keep.
"""
import time
import urllib.request


def _touch(url: str, delay_s: float = 0.0):
    """Simulate a provider dereferencing a link found inside a prompt it
    logged or forwarded, the way Dragos's compromised providers did."""
    if delay_s:
        time.sleep(delay_s)
    try:
        urllib.request.urlopen(url, timeout=2)
    except Exception:
        pass


def provider_clean(prompt: str, canary: dict, zdr: bool):
    """Honors ZDR. Never touches the canary regardless of the flag."""
    return {"provider": "clean-direct", "zdr_requested": zdr, "forwarded_to": None}


def provider_logs_anyway(prompt: str, canary: dict, zdr: bool):
    """The Together/Phala failure mode: a background logging or debug
    pipeline reads the prompt after the response is returned, ZDR flag or
    not. The delay mirrors Dragos's finding that hits often land hours to
    days after the original request."""
    _touch(canary["url"], delay_s=0.3)
    return {"provider": "logs-anyway", "zdr_requested": zdr, "forwarded_to": None}


def provider_undisclosed_hop(prompt: str, canary: dict, zdr: bool):
    """The Novita/OpenRouter failure mode: the request is quietly forwarded
    to a second, undisclosed provider that also sees the prompt, and that
    second hop is the one that touches the canary."""
    _touch(canary["url"], delay_s=0.1)
    return {"provider": "router-A", "zdr_requested": zdr, "forwarded_to": "undisclosed-hop-B"}


PROVIDERS = {
    "clean-direct": provider_clean,
    "logs-anyway": provider_logs_anyway,
    "router-A": provider_undisclosed_hop,
}


def route_request(provider_name: str, prompt: str, canary: dict, zdr: bool = True):
    handler = PROVIDERS[provider_name]
    return handler(prompt, canary, zdr)
