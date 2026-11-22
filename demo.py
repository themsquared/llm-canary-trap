"""Run the canary trap end to end:

1. Start a local callback listener (stand-in for the canary collector).
2. Mint one canary per mock provider and send a ZDR-flagged request through
   each.
3. Wait briefly for any out-of-band hits (logging pipelines don't fire
   synchronously).
4. Report which providers touched their canary despite the ZDR flag, same
   verdict shape as Dragos's "stolen keys" table.
"""
import time

from callback_server import dump_hits, start_server
from canary_mint import build_poisoned_prompt, mint_canary
from mock_gateway import PROVIDERS, route_request

PORT = 8743
WAIT_FOR_ASYNC_HITS_S = 1.5


def main():
    server, hits = start_server(PORT)
    base_url = f"http://127.0.0.1:{PORT}"
    print(f"canary listener up on {base_url}\n")

    canaries = {}
    for provider_name in PROVIDERS:
        canary = mint_canary(base_url)
        prompt = build_poisoned_prompt(canary)
        result = route_request(provider_name, prompt, canary, zdr=True)
        canaries[canary["token"]] = provider_name
        print(f"sent ZDR-flagged request to {provider_name!r}: {result}")

    print(f"\nwaiting {WAIT_FOR_ASYNC_HITS_S}s for any out-of-band callbacks...")
    time.sleep(WAIT_FOR_ASYNC_HITS_S)

    dump_hits(hits)
    hit_tokens = {h["token"] for h in hits}

    print("\nverdict (ZDR was requested on every row):")
    print(f"{'provider':<16} {'canary touched?':<16} {'hit count'}")
    for token, provider_name in canaries.items():
        touched = token in hit_tokens
        count = sum(1 for h in hits if h["token"] == token)
        flag = "LEAKED" if touched else "honored"
        print(f"{provider_name:<16} {flag:<16} {count}")

    server.shutdown()


if __name__ == "__main__":
    main()
