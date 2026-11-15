# Git Pack Manager — Modrinth server

Prepared 15 November 2026. Official guide: https://git-pack-manager.docs.cursedmods.com/guides/setup/

## Confirmed server settings

Read through Cyberduck from the live server configuration:

- MESH Lib `httpPort`: `20315`; `exposedPort`: `20315`; `!!!version`: `0`.
- Git Pack Manager public IP: `185.83.154.202`.
- Repository URL: `https://github.com/physicalism/realms-beyond-respack.git`.
- Resource-pack provider enabled; root `/resourcepacks`.
- Datapack provider disabled. Leave it disabled to retain existing world datapack management.
- Repository branch is now `server-pack`; updated through Cyberduck and saved before restart.

The main source repository has its pack at the repository root, whereas Git Pack Manager expects individual packs inside its configured resource-pack directory. Both unpacked folders and priority-prefixed ZIPs are supported; a ZIP is not intrinsically required.

## Distribution

`.github/workflows/server-pack.yml` validates and builds the pack on relevant pushes to `main`, or manual workflow dispatch. It writes `resourcepacks/0-realms-beyond.zip` and `SOURCE_COMMIT` to the separate `server-pack` branch. It does not bump versions, create releases, or relocate live source. It uses a normal push, without force, and serialises runs.

This distributes committed source changes automatically; it is not restricted to published GitHub Releases. Existing uncommitted source edits will not be distributed until deliberately committed and pushed.

## Activation procedure

1. Review and commit the workflow, model fix, and intended source changes, then push to `main`. Do not blindly include unrelated pending work.
2. Confirm the GitHub Actions run succeeds and `server-pack/resourcepacks/0-realms-beyond.zip` exists.
3. In server `config/git-pack-manager/main.json`, change only `repositoryInfo.branch` to `server-pack`. Keep rootLocation `/resourcepacks`, the existing URL pattern, and the confirmed port values.
4. Restart the server, then run `git-pack-manager trigger-update` in its console. Check for successful clone and resource-pack generation.
5. On GitHub repository Settings → Webhooks, add payload URL `http://185.83.154.202:20315/git-pack-manager/` with push events. The official mod accepts POSTs as update triggers. It checks for changes to its configured branch. Verify a successful delivery after the server starts.
6. Join and use `/git-pack-manager request-pack`. Confirm the downloaded pack and the lily-pad fix in-game, including Complementary shaders. Avoid loading a stale local Realms Beyond copy above the server pack while testing.

A webhook on this repository receives the distribution branch push as well as the source push, so the second notification lets the server fetch the newly built ZIP. Failed Actions builds leave the previous server pack intact. Existing GitHub rules may prevent Actions from pushing; inspect the first run rather than assuming success.

## Status

Activated on 15 November 2026. Source commit `3d3065603dab0159621ac50eaa3f18e855143034` was pushed to main. GitHub Actions generated `server-pack`, with SOURCE_COMMIT matching that source commit. The live server config was changed to `server-pack`, webhook 712350502 was created for push events, and the server was restarted through the Modrinth web dashboard.

The server generated `4976881525863590517.zip` (8.5 MB). Its public HTTP download succeeded; all 2,449 downloaded asset files matched committed source byte-for-byte, including the five inset lotus centres. Safari automatically extracted the verification download. The pack format and version remain unchanged. Other pending working-tree changes, including the This Rocks work, were deliberately left uncommitted and are not part of this deployment.

The existing server clone retained its local branch name `main` and generated a local merge when pulling `server-pack`; the downloaded contents nevertheless match the distribution source exactly. Do not infer pack contents from the branch name printed in these server logs. Log messages about an absent nested `packs` directory did not prevent the complete pack being assembled; download verification establishes the resulting contents.

Local validator, clean committed-source build, and distribution shell checks passed. In-game shader appearance still needs Henry's check. No version bump or GitHub Release was created.

## Ongoing source hygiene and build identity

Normal updates require committing and pushing to `main`; a release tag and Loader update are not required. The base release remains 0.1.57 until Henry requests a numbered release. Automatic builds display the source commit after the version and record its full SHA in `pack.mcmeta` under `realms_beyond.source_commit`. `SOURCE_COMMIT` on the distribution branch is the corresponding full revision. Local development builds keep the ordinary base-version label unless `REALMS_BEYOND_BUILD_COMMIT` is explicitly supplied.

GitHub reported webhook deliveries as failed with the message “OK”, but the server logged successful WEBHOOK update checks at the matching push/redelivery times (21:43:02 and 21:43:05 on 15 November). A manual trigger also succeeded at 21:43:35. The response-reporting quirk remains unresolved; receipt and update execution were verified independently.

The later lotus petal correction is source commit `26a987e`; its distribution branch SOURCE_COMMIT was verified after the automatic build. This does not establish in-game visual approval. The subsequent source-hygiene commit records the existing nature work too; use its Git SHA rather than this historical initial-build ZIP filename to identify future builds.
