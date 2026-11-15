# Git Pack Manager — Modrinth server

Prepared 15 November 2026. Official guide: https://git-pack-manager.docs.cursedmods.com/guides/setup/

## Confirmed server settings

Read through Cyberduck from the live server configuration:

- MESH Lib `httpPort`: `20315`; `exposedPort`: `20315`; `!!!version`: `0`.
- Git Pack Manager public IP: `185.83.154.202`.
- Repository URL: `https://github.com/physicalism/realms-beyond-respack.git`.
- Resource-pack provider enabled; root `/resourcepacks`.
- Datapack provider disabled. Leave it disabled to retain existing world datapack management.
- Current repository branch setting is `main`; change it to `server-pack` only after the distribution branch exists.

The main source repository has its pack at the repository root, whereas Git Pack Manager expects individual packs inside its configured resource-pack directory. Both unpacked folders and priority-prefixed ZIPs are supported; a ZIP is not intrinsically required.

## Distribution

`.github/workflows/server-pack.yml` validates and builds the pack on relevant pushes to `main`, or manual workflow dispatch. It writes `resourcepacks/0-realms-beyond.zip` and `SOURCE_COMMIT` to the separate `server-pack` branch. It does not bump versions, create releases, or relocate live source. It uses a normal push, without force, and serialises runs.

This distributes committed source changes automatically; it is not restricted to published GitHub Releases. Existing uncommitted source edits will not be distributed until deliberately committed and pushed.

## Activation still required

1. Review and commit the workflow, model fix, and intended source changes, then push to `main`. Do not blindly include unrelated pending work.
2. Confirm the GitHub Actions run succeeds and `server-pack/resourcepacks/0-realms-beyond.zip` exists.
3. In server `config/git-pack-manager/main.json`, change only `repositoryInfo.branch` to `server-pack`. Keep rootLocation `/resourcepacks`, the existing URL pattern, and the confirmed port values.
4. Restart the server, then run `git-pack-manager trigger-update` in its console. Check for successful clone and resource-pack generation.
5. On GitHub repository Settings → Webhooks, add payload URL `http://185.83.154.202:20315/git-pack-manager/` with push events. The official mod accepts POSTs as update triggers. It checks for changes to its configured branch. Verify a successful delivery after the server starts.
6. Join and use `/git-pack-manager request-pack`. Confirm the downloaded pack and the lily-pad fix in-game, including Complementary shaders. Avoid loading a stale local Realms Beyond copy above the server pack while testing.

A webhook on this repository receives the distribution branch push as well as the source push, so the second notification lets the server fetch the newly built ZIP. Failed Actions builds leave the previous server pack intact. Existing GitHub rules may prevent Actions from pushing; inspect the first run rather than assuming success.

## Status

Local validator passed for the lily-pad model fix. Distribution shell tested against a temporary local Git remote for initial branch creation and a subsequent update; both passed. Workflow not run on GitHub. Server settings inspected, not changed; no restart or webhook creation performed. No commit, push, release, or version bump performed. Distribution and in-game appearance remain unverified.
