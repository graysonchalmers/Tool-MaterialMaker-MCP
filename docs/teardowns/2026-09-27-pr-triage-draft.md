# Triage and reply drafts for waskosky's PRs (#7, #8, #13)

**Nothing here has been posted, merged or run.** Every action below needs Grayson's go.

The PRs were read with `gh pr view` / `gh pr diff` only. Lens C read their bug claims against `main`, and reproduced two of them (#7 and #13) with its own pure-Python scripts; it did not run the contributor's code. All three bugs are real.

## Recommended order

1. **#13 sweep publication.** Merge after changes. It is narrow and good: staging directory, an exact frame-set check, a decode check, and an atomic `os.replace` publish.
   - **The one required change:** it drops the `heightmap_path`/`heightmap_scale` forwarding that `main` added after their base (commits `9e0cd99`, `559c0b9`). That forwarding has to be restored before merging, or Deep Parallax's `parallax_spin` silently breaks.
   - **Before merging:** rebase onto `main`, then run the integration sweep tests on Windows.
   - **Expect conflicts.** Today's truth pass touched `render.py` and `preview.py`, which #13 also changes, so the rebase will conflict there too.
2. **#7 play download snapshots.** Merge after changes. It gives each render its own snapshot directory plus a receipt, uses a validated preview id (so no path traversal), and ignores stale responses.
   - **The one required change:** prune old snapshots, e.g. keep the last 20. Without it `output/play/previews/` grows without bound.
   - **Before merging:** rebase, then run a hands-on `play.bat` pass on Windows.
3. **#8 render publication.** Close as superseded, with credit.
   - **Its intent landed in the truth pass (`fdd2ac7`, on the branch, not merged yet):** a render now fails on a nonzero exit or any PNG that doesn't decode, and the outdir is forced absolute.
   - **As written it would break every real render.** Its size check assumes MM honours `--size`, but MM always bakes at 2048.

**CI note.** GitHub holds workflows on first-time-contributor PRs until a maintainer clicks "Approve and run". That is why none of the three shows any checks.

## Draft replies (Grayson's voice; edit freely)

**#13**
> Thanks for this, and sorry for the slow reply. Nobody here was watching the PR queue, and that's on us. The bug is real (we reproduced the partial-frame and delete-before-render cases) and the fix is the right shape. One thing before merging: `main` has since added `heightmap_path`/`heightmap_scale` forwarding to the sweep command for a Deep Parallax preview mode, and this branch drops it. Could you rebase and keep that forwarding? Or say the word and we'll do the rebase on our side. We'll run the Windows integration sweep tests before merging.

**#7**
> Thanks. This is a real round-trip bug: the download was exporting the untweaked graph next to maps from a different render, and we reproduced it. The per-render snapshot design is good. One request: could the snapshot directory prune old entries (keep the last ~20)? Otherwise `output/play/previews/` grows forever. After a rebase we'll do a hands-on Windows pass with `play.bat` and merge.

**#8**
> Thank you. This found a real problem: a nonzero Godot exit with a fresh PNG was reported as success. We've landed a narrower fix (`fdd2ac7`, merging to `main` shortly): renders now fail on a nonzero exit or any PNG that doesn't decode, and the output dir is forced absolute. We're closing this one rather than merging, for one reason we only understood while looking at it: Material Maker at our pinned commit ignores `--size` and always bakes at 2048, so the size check here would have failed every real render on Windows. `size` is now honoured by downsampling after export. Credit to you for finding it.

## Also worth saying (optional, all three)
> We noticed your fork's `integration/next` (the "Material Workshop" direction). If you want any of that upstream, open an issue first so we can talk about scope. This project is small and "me-first" by design, but a second person using it is genuinely valuable.
