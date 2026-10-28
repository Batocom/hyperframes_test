# Troubleshoot — expected failures & fixes

Real failure modes from the production pipeline this sample came from. Check here
before inventing theories.

## Media resolve (media-use / HeyGen)

| Symptom | Cause | Fix |
|---|---|---|
| `resolve --doctor` fails / 401 | No HeyGen credential | `export BROWSER=none; heygen auth login --oauth` (see `docs/KEYS.md`), or set `HEYGEN_API_KEY` |
| SFX results all dropped | Default score floor 0.7 too strict for named effects | The resolver uses a 0.4 floor; if you call `searchSounds` yourself, pass `minScore: 0.4` |
| Poor SFX match | Vague query | Concrete physical description: "gunshot bang rifle single shot", not "weapon sound" |
| BGM missing at render | Async generate still running (`bgm_pending: true`) | `npx hyperframes … wait-bgm.mjs --audio-meta audio_meta.json` → check `bgm_status.json`; failed BGM is omitted, never blocks |
| Music drowns narration | Bed volume too high | Bed default ≈ 0.12 (−18 dB) under voice; override per-cue `volume` in `audio_meta.json` |

## Transcription (Groq whisper)

| Symptom | Cause | Fix |
|---|---|---|
| HTTP 404 / model not found | Groq delists models (e.g. llama-3.3-70b gone) | `GET /openai/v1/models`, pick an available one; whisper large-v3/turbo for ASR |
| Transcript `words: []` | Some whisper responses omit word timings | Save the **full** response; use `segments` for positioning, or re-request with word timestamps explicitly |
| 400 tool-schema / invalid model | Model string wrong or empty | Pin explicitly per call; never rely on provider default |

## Composition / render (HyperFrames)

| Symptom | Cause | Fix |
|---|---|---|
| Preview refresh → `ERR_CONNECTION_TIMED_OUT` | Foreground `npm run dev` died with its session | `npx hyperframes preview --background`, verify `--status`, `--stop` when done |
| `lint`: element never visible | Missing `data-start` (it's what marks an element timed) | Add `data-start` + duration; keep `class="clip"` for the full-frame box |
| Render differs between runs | Nondeterminism | Ban `Date.now()`, `Math.random()`, network fetches; timelines must be paused + registered on `window.__timelines` |
| Audio not in render | Video element carries picture only | `muted` video + separate `<audio>` element for the track |
| Pinned CLI is stale | `package.json` pins exact version | `npx hyperframes@latest upgrade --project . --check` → review delta → `--project .` |

## Mux / delivery (ffmpeg)

| Symptom | Cause | Fix |
|---|---|---|
| Output has wrong/no audio or video | Implicit stream selection | Always explicit: `-map 0:v:0 -map 1:a:0` |
| "Looks fine" but file corrupt | Never decoded it | `ffmpeg -v error -i out.mp4 -f null -` must be silent; then ffprobe frame count |
| Loudness complaints | No gate | Check `ebur128`: target ≈ −12.7 LUFS, TP < −0.7 dBTP |
| Re-render changed scenes you didn't touch | Accidental scope creep | PSNR-diff unchanged time ranges vs the previous cut (expect `inf`) before muxing |

## Kaggle-side (when this workflow runs in a notebook)

| Symptom | Cause | Fix |
|---|---|---|
| `kernels_logs` / `kernels_output` empty while RUNNING | API returns nothing mid-run | Poll the live dataset outputs instead; logs often only settle after completion |
| Push while kernel RUNNING | Queues a second run | To force restart: `kernels_delete` then push |
| 12h kernel cap / no auto-restart | Platform limit | Re-run All manually; persist via datasets (chat DB / artifacts) |
| ngrok interstitial `ERR_NGROK_6024` | Once-per-browser warning page | Render the interstitial first, click Visit Site, *then* set auth headers — stale auth on the interstitial breaks it |
