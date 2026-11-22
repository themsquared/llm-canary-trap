# llm-canary-trap

A stdlib-only, 60-second reproduction of the detection technique behind
this week's biggest AI-supply-chain finding: catching an inference
provider that ignores a Zero Data Retention (ZDR) flag, not by asking it
nicely, but by seeding every outbound prompt with a unique tripwire and
watching for the callback.

**The real finding this reproduces the shape of:** Dragos (HD Moore, Chief
Research Officer) sent nearly 2 million prompts containing unique [Thinkst
Canarytokens](https://canarytokens.org/) URLs and fake AWS credentials to
widely used AI providers and routers over July-November 2026, then watched
what touched them. Writeup: ["Three breaches, endless leaks: Your AI
supply chain needs
canaries"](https://www.dragos.com/blog/ai-supply-chain-security-canary-tokens)
(2026-11-19). Findings: three providers were actively compromised and
attackers used the stolen AWS keys for tens of thousands of AWS API calls;
inference marketplace resellers read and retained customer prompts using
nothing more than standard request logging; and ZDR flags were ignored
outright, including prompts sent to U.S.-based providers that ended up
accessed from inside a Chinese AI lab, and one canary link that surfaced
in an internal company chat 24 days after the original request.

Days later, [OpenRouter published its own
response](https://openrouter.ai/blog/announcements/data-processing-incidents-on-inference-providers/)
(2026-11-22): it off-boarded 3 providers and pulled 125 endpoints from ZDR
eligibility, and named three of them with their own public incident
posts: [Novita](https://novita.ai/blog/minimax-requests-privacy-notice/)
(a routing-config bug silently forwarded MiniMax-model requests to
MiniMax's own API from 2026-05-28 to 2026-11-11), Phala (a real breach via
an unauthenticated loopback management interface, exposure window
2026-10-21 to 2026-11-08), and Together (their own AI coding agent leaked
a Hugging Face credential into a public repo, which an attacker used to
pull stored prompt samples).

## What this is, and is not

This repo does **not** talk to any real AI provider, store any real
prompt, or use any real credential. It is a miniature, fully synthetic
version of Dragos's canary-seeding technique, built to show the
mechanism: mint a unique, otherwise-unreachable URL per outbound request,
bury it in the prompt, and treat any callback hit as proof that something
downstream read and acted on content it was told not to retain or forward.
Three mock "providers" stand in for the three failure modes documented
this week:

- `clean-direct` honors the ZDR flag and never touches its canary.
- `logs-anyway` is the Together/Phala shape: a background logging or
  debug path reads the prompt after the response is returned, flag or no
  flag.
- `router-A` is the Novita/OpenRouter shape: the request is quietly
  forwarded to a second, undisclosed hop, and that hop is the one that
  touches the canary.

## Architecture

```
demo.py
  |- callback_server.py   stdlib ThreadingHTTPServer, logs GET /canary/<token>
  |- canary_mint.py       mints one unique URL + fake AWS key per request
  `- mock_gateway.py      3 mock providers, each simulating one failure mode
```

`demo.py` starts the listener, sends one ZDR-flagged request through each
mock provider, waits briefly for any out-of-band callback (Dragos's real
hits often landed hours to days later; this demo's delay is milliseconds
so it fits in a terminal), then prints a verdict table and writes
`canary_hits.jsonl`.

## Quickstart

Requires Python 3.9+, no dependencies.

```bash
git clone https://github.com/themsquared/llm-canary-trap.git
cd llm-canary-trap
python3 demo.py
```

Expected output:

```
canary listener up on http://127.0.0.1:8743

sent ZDR-flagged request to 'clean-direct': {'provider': 'clean-direct', 'zdr_requested': True, 'forwarded_to': None}
sent ZDR-flagged request to 'logs-anyway': {'provider': 'logs-anyway', 'zdr_requested': True, 'forwarded_to': None}
sent ZDR-flagged request to 'router-A': {'provider': 'router-A', 'zdr_requested': True, 'forwarded_to': 'undisclosed-hop-B'}

waiting 1.5s for any out-of-band callbacks...

verdict (ZDR was requested on every row):
provider         canary touched?  hit count
clean-direct     honored          0
logs-anyway      LEAKED           1
router-A         LEAKED           1
```

Every row requested ZDR. Two of three mock providers touched their canary
anyway, which is exactly the point: a ZDR flag is a policy you ask a
provider to honor, not a control you can verify from your own side of the
request, unless something is watching for it to be broken.

## Why this matters past the demo

The providers named this week were not caught by an internal audit of
their own privacy policy. Dragos caught them by testing the "zero data
retention" claim directly: seeding real requests with a unique marker and
checking, independently, whether anything downstream touched it. Any team
routing prompts through a shared gateway or router can run the same check
at a much smaller scale than Dragos's 2 million prompts, the same way
`clean-direct` vs `logs-anyway` vs `router-A` model the three outcomes
here.

## License

Apache-2.0. See [LICENSE](LICENSE).
