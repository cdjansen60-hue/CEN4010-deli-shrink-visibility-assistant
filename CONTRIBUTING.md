# Contributing

This is a course project (CEN 4010, FAU), but it is set up so others can run and extend it.

## Getting started

1. Fork and clone the repository.
2. Create a virtual environment and run `pip install -r requirements.txt`.
3. Run `pytest` to confirm the tests pass before making changes.

## Making changes

- Keep each commit to one logical change, with a message that says what changed and why.
- Add or update a test with every behavior change. Tests must use the mock event interpreter and must never call the real API.
- Keep thresholds and windows in the config file, not in code.
- Use synthetic data only. Do not commit real store data, credentials, or `.env` files.

## Scope

The system flags lots at risk of expiring unsold and leaves every decision to the manager. Changes that order, mark down, rotate, or discard stock, or that connect to ordering, POS, or pricing systems, are out of scope.

## Pull requests

Describe what changed, why, and how you tested it. If a change departs from the Solution Design Report, say so and give the reason.
