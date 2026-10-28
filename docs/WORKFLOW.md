# Workflow — brief to verified MP4

The production loop this workspace encodes. Skills first, check after every edit,
never trust a render you haven't decoded.

## 0. Orient

- Agent contract: `AGENTS.md` (skills routing, composition rules).
- Intent routing: the `/hyperframes` skill decides which workflow fits
  (launch video, explainer, captions, motion graphic, music-to-video, …).
- Missing/stale skills: `npx hyperframes skills update <name>` (restart session after).

## 1. Media (BGM / SFX / images)

```bash
npx hyperframes media-use resolve --doctor          # verify auth before resolving
./scripts/resolve_media.sh bgm "dark cinematic tension documentary underscore"
./scripts/resolve_media.sh sfx "gunshot bang rifle single shot"
```

- Assets land in the project `.media/` (or `assets/`) with a `manifest.jsonl`
  provenance record (provider, prompt, score). Re-runs reuse the cache.
- Name SFX concretely ("glass shatter", not "dramatic sound") — vague queries score low.
- SFX search floor is 0.4 (whoosh-family scores ~0.5–0.67; the API default 0.7 drops most).
- BGM under narration is a **bed** (default vol ~0.12); silent films ~0.9.
- If BGM is generating asynchronously: `npx … wait-bgm.mjs` (writes `bgm_status.json`) before render.
- Stock photos/videos: `$PEXELS_API_KEY` → any script hitting `api.pexels.com`
  (or the OpenChatCut `search_stock_media` tool when running there).

## 2. Author

- `index.html` = root timeline; sub-scenes in `compositions/` via `data-composition-src`.
- Every timed element: `data-start` + duration, `class="clip"`.
- Timelines **paused** and registered: `window.__timelines["id"] = gsap.timeline({ paused: true })`.
- Videos `muted` + separate `<audio>` for sound.
- **Deterministic only**: no `Date.now()`, `Math.random()`, network fetches.

## 3. Check loop (never skip)

```bash
npm run check        # lint + runtime + layout + motion + contrast
```

Fix all errors; review warnings before rendering. Machine-readable: `npx hyperframes lint --json`.

## 4. Preview (agent-safe)

```bash
npx hyperframes preview --background   # persistent Studio preview
npx hyperframes preview --status       # confirm listening
npx hyperframes preview --stop         # stop after review
```

Do NOT background `npm run dev` — it dies with the session and leaves dead refreshes.

## 5. Render

```bash
npm run render       # → renders/<name>_<timestamp>.mp4
```

- CLI is pinned in `package.json`; upgrade deliberately:
  `npx hyperframes@latest upgrade --project . --check` then `… --project .`.

## 6. Verify (a render is not done until it passes)

1. **Decode clean**: `ffmpeg -v error -i out.mp4 -f null -` → empty stderr, exit 0.
2. **Frame count**: `ffprobe -count_frames … nb_read_frames` matches expected (fps × duration).
3. **Audio gates** when narration was muxed (`scripts/verify_mux.py` does all of this):
   - mux with explicit maps: `-map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k`
   - loudness ≈ −12.7 LUFS, true peak < −0.7 dBTP (`ebur128`)
4. **Change proof**: after re-rendering one scene, PSNR-diff the unchanged regions
   vs the previous cut (expect `inf`), changed region (expect finite).

## 7. Post-production audio pattern (documentary-style)

1. User records narration → word-level transcript (Groq whisper: save **full**
   response including `segments`; `words` may come back empty — see TROUBLESHOOT).
2. Cue times come from word timings + scene HTML event times (typing cues, cuts).
3. Stems: `stem_bed.wav` (BGM, ducked under speech) + `stem_sfx.wav` (cue-aligned),
   mixed to `mix_raw.wav` → limited `mix_lim.wav`.
4. Mux narration mix onto the video-only cut via `scripts/verify_mux.py`.
5. Open the artifact and listen at cue boundaries — RMS probes are necessary, not sufficient.
