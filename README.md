# TurnCraft / Voice Agent Lab

![Tests](https://github.com/Hemanth-TS/turncraft-voice-agent/actions/workflows/tests.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-3776AB)
![License](https://img.shields.io/badge/license-MIT-22c55e)

An asynchronous conversational workflow simulator with interruption handling, tool routing and traceable state transitions.

> **New portfolio demo · created 30 October 2026.** This is an original,
> AI-assisted implementation created for this portfolio. It is not a past
> client delivery, production deployment, or evidence of commercial results.
> All supplied data is synthetic. No popular project was copied or forked.

## Run in under a minute

Only Python 3.11 or later is required. No API keys, model downloads,
paid services or third-party Python packages are needed.

```sh
git clone https://github.com/Hemanth-TS/turncraft-voice-agent.git
cd turncraft-voice-agent
python turncraft.py
python -m unittest discover -s tests -v
```

## What it demonstrates

`Event → serialized reducer → calendar tool → cancellable speech task → trace`

- Barge-in cancels an in-flight synthetic speech task.
- Calendar tools use timeouts, conflict checks and idempotency keys.
- Booking is gated by an explicit structured confirmation event.
- A human-handoff path and graceful session closure are observable in JSON.

The sample lists two fictional slots on 10 January 2030, books one, requests
a human, then closes. The receipt is `demo-001`.

## Integration boundary

This models conversational orchestration patterns similar to those used in
LiveKit-based agents. **It does not integrate LiveKit, handle real audio,
run an LLM, make phone calls or connect a real calendar.** `Tools` is an
async protocol intended as an integration seam. A real adapter also needs
authentication, persistent idempotency, timezone handling, privacy controls,
and cancellation propagation. Tools run inside the event lock; an active tool
call can delay barge-in until its timeout. Streaming tool cancellation is future work.

The deterministic CLI replay drains speech between events; the interruption
behavior is exercised directly by the async regression test. Intent routing
is deliberately a small keyword rule, not a claim of language understanding.


## Repository guide

- `turncraft.py`: implementation and command-line interface.
- `samples/`: fictional input fixtures; safe to edit and reuse.
- `tests/`: regression tests, including boundary cases.
- `.github/workflows/tests.yml`: automated Windows/Linux checks.
- [CHANGELOG.md](CHANGELOG.md): release notes.
- [CONTRIBUTING.md](CONTRIBUTING.md): development and bug-report guidance.

## Maintenance and provenance

Version **0.1.0** is an educational demo, with no production support commitment.
Changes should include a regression test and an entry in the changelog.
Algorithms are implemented directly in this repository; there are no vendored
models, third-party source files, proprietary assets or external datasets.
Badges show GitHub's current CI status; sample outputs are not independent benchmarks.

[Portfolio](https://hemanth-ts.github.io/) · [MIT license](LICENSE)
