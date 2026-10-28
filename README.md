# HyperFrames Agent Workspace (sample)

A working **HyperFrames composition project** plus the workflow docs, helper scripts,
and container setup an AI agent needs to produce, check, render, and verify videos
end-to-end. Shipped from a real production pipeline (a 7-scene Swahili documentary
episode: narration mux, SFX/BGM stems, LUFS-gated mixes).

## What's here

| Path | What it is |
|---|---|
| `index.html` + `compositions/` | The sample project: a 9-scene composition (sub-compositions via `data-composition-src`) |
| `AGENTS.md` | **Agent contract** — skills-first routing, commands, key composition rules. Read this first. |
| `docs/WORKFLOW.md` | End-to-end pipeline: brief → media → author → check → preview → render → verify |
| `docs/KEYS.md` | Every secret this workspace expects, what it powers, where to rotate it |
| `docs/TROUBLESHOOT.md` | Expected failures and their fixes (real ones from production) |
| `scripts/resolve_media.sh` | One-shot BGM/SFX/image fetch via `media-use resolve` (HeyGen catalog) |
| `scripts/verify_mux.py` | Mux narration onto video with explicit stream maps + decode/frame gates |
| `verify_composition.py` | Project-specific structural verifier for this sample |
| `.devcontainer/` | Codespace/devcontainer: Node 20, Python, ffmpeg, hyperframes + heygen CLIs |

## Quickstart (in a Codespace)

```bash
npm i -g hyperframes@0.8.38     # if post-create didn't run
npm run check                    # lint + runtime + layout + motion + contrast
npx hyperframes preview --background   # agent-safe Studio preview
npm run render                   # → renders/<name>_<timestamp>.mp4
```

Media fetch (needs `GROQ_API_KEY` / HeyGen auth — see `docs/KEYS.md`):

```bash
./scripts/resolve_media.sh bgm "dark cinematic tension documentary underscore"
./scripts/resolve_media.sh sfx "gunshot bang rifle single shot"
```

## Secrets

Keys live in **repository Codespaces secrets** (Settings → Secrets → Codespaces),
never in git. Inside a codespace they appear as plain env vars
(`$PEXELS_API_KEY`, `$GROQ_API_KEY`, …). The contract for agents is `.env.example`;
the rotation map is `docs/KEYS.md`.

## Rules for agents

1. Read `AGENTS.md` before touching any composition.
2. `npm run check` must pass before claiming a change is done.
3. Renders are never "done" until decoded and frame-counted (`docs/WORKFLOW.md` § Verify).
4. No secrets in commits, logs, or composition files. Ever.
