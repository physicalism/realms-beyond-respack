# Resource pack entry point

Read [CLAUDE.md](CLAUDE.md) before changing this pack. It is the shared source of pack-specific development and visual rules for all assistants; do not maintain a competing copy here.

Use [docs/FEATURES.md](docs/FEATURES.md) to locate the relevant generator and [README.md](README.md) for documented item commands and placement. Read only the sections relevant to the current task.

From this directory, validate asset changes with `python3 tools/build.py --check`. Build, installation, and publication are separate actions. Follow the release restrictions in CLAUDE.md and the user's current instructions.

Preserve any existing uncommitted work. Do not run a generator merely to inspect it: its outputs may immediately change the live-linked pack.

## Henry's publishing preference

When asked to publish, prepare and validate the release, then give Henry a simple terminal command to push and publish using `gh`; avoid requiring the GitHub website. Do not publish while visual refinements are still underway. A Git push alone does not publish a release.
