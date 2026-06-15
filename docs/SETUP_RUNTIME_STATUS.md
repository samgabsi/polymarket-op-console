# Runtime and Virtual Environment Status v1.9.0-real

The runtime status page at `/setup/status` is read-only guidance.

It is organized into sections:

- App
- Python
- Virtual Environment
- Launch
- Filesystem
- Environment
- Dependencies
- Restart Status

Each section shows detected values, recommended/expected values, and status badges.

## What it can do

- show Python version
- show app version
- show whether a venv is detected
- show dependency import availability
- show expected launch command
- show current working directory
- show runtime data directory
- show `.env` and `.env.example` status
- show process-vs-saved `.env` differences
- show copyable setup commands

## What it cannot do

The page does not execute shell commands, run pip, install packages, mutate the virtual environment, or turn user input into a command line.
