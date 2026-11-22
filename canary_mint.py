"""Mint unique canary tokens for outbound LLM prompts.

Each canary is a URL that exists nowhere except inside one prompt. If the
listener ever sees a hit on it, something downstream read that prompt's
contents and dereferenced the link: a provider, a reseller, a logging
pipeline, a background scraper. The prompt itself never says what the link
is for, the same way Dragos's canary tokens didn't.
"""
import secrets
import time


def mint_canary(callback_base: str) -> dict:
    token = secrets.token_hex(8)
    fake_access_key = "AKIA" + secrets.token_hex(8).upper()[:16]
    return {
        "token": token,
        "url": f"{callback_base}/canary/{token}",
        "fake_aws_key": fake_access_key,
        "minted_at": time.time(),
    }


def build_poisoned_prompt(canary: dict) -> str:
    """A prompt that looks like an ordinary support ticket, with a canary
    buried in it the way Dragos buried URLs and AWS keys in real traffic."""
    return (
        "Can you help me debug this deploy script? Here is the config "
        "I'm using, including the staging credentials:\n\n"
        f"AWS_ACCESS_KEY_ID={canary['fake_aws_key']}\n"
        f"AWS_SECRET_ACCESS_KEY=not-a-real-secret-{canary['token']}\n"
        f"DEBUG_LOG_URL={canary['url']}\n\n"
        "It keeps failing on step 3, any idea why?"
    )
