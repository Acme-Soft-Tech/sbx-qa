# sbx-qa — agent guidance

The file the real QA repo does not have. Its conventions currently live only as comments
inside `pytest.ini` and `conftest.py`, which an agent may or may not read.

## Layout

- **`conftest.py` at the repo root.** Not in `tests/`. Moving it breaks fixtures subtly.
- **PascalCase test filenames**: `test_Smoke_Class.py`, `test_Regression_Class.py`.
- **One class per file.** No exceptions.
- **Helpers live in `wizard_helpers.py`.** Import them; never keep a local copy.

## The SMS rule — the one that matters

Anything reaching "Send code" **must** carry `@pytest.mark.flaky(reruns=0)`.

`pytest.ini` sets a global `--reruns 2`. A flaky retry on an SMS test sends a second real
message nobody counted. In the sandbox that is a row in `sent_messages`; in production it
is a text to a person.

Adding an SMS-reaching test without that marker is the single worst change you can make
in this repo.

## Markers

`smoke` · `regression` · `e2e` · `ui`

PR and agent runs are `-m "smoke or regression"`. `e2e` is blocked by `sms-guard.sh`
unless a human sets `SBX_ALLOW_SMS=1` for one command.

## Base URL

`SBX_BASE_URL` is **required** and has no default. G4 points it at a per-PR preview.
If it is unset, stop — do not guess a host. An unset base URL means the suite tests
nothing while reporting green.

## Never

- Never widen a marker expression to make a run "more thorough".
- Never edit a test to make it pass. If a test is red, the source is wrong until the
  committed `spec.md` says otherwise. `test-freeze.sh` blocks the edit.
- Never commit `__pycache__`. Ignore rules do not untrack what is already tracked.
