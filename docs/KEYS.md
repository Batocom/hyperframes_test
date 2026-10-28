# Keys — what, where, rotation

Values live in **repository Codespaces secrets** (public repo → Settings → Secrets →
Codespaces). Codespaces injects them as env vars into every codespace of this repo.
They are never committed; `.env.example` is the name contract only.

> This repo is PUBLIC. Anything committed here is world-visible. Secrets only via
> the secrets store. If a key ever lands in a commit: rotate it immediately at the
> provider, then scrub history (`git filter-repo`) — but prefer never.

## Secrets in this repo

| Env var | Powers | Consumer | Rotate at |
|---|---|---|---|
| `PEXELS_API_KEY` | Stock photo/video search (`api.pexels.com`) | OpenChatCut `search_stock_media`; any script hitting the API | <https://www.pexels.com/api/> |
| `GROQ_API_KEY` | Whisper transcription, quick LLM checks | Transcription scripts, `docs/WORKFLOW.md` §7 | <https://console.groq.com/keys> |

## Not a secret — needs interactive login

### HeyGen (BGM / SFX / image / icon catalog)

The media catalog path (`media-use resolve`) rides the HeyGen CLI **OAuth free
allowance**. OAuth tokens cannot be pre-seeded as repo secrets. Inside a codespace:

```bash
export BROWSER=none HEYGEN_NO_BROWSER=1   # print the sign-in URL instead of opening a browser
heygen auth login --oauth                # copy the printed URL to YOUR browser, sign in
heygen auth status                       # expect: type oauth, plan free
```

Token refreshes automatically; if it dies, re-run the login. Alternative: create an
API key at <https://platform.heygen.com/api-keys> and set it as a
**`HEYGEN_API_KEY`** Codespaces secret (env var takes precedence over the stored
credential) — note this bills **API credits** instead of the free OAuth allowance.

Verify the whole media path:

```bash
npx hyperframes media-use resolve --doctor
```

## Managing secrets from the CLI

List:      `gh api repos/Batocom/hyperframes_test/codespaces/secrets --jq '.secrets[].name'`
Add/rot:   repo → Settings → Secrets → Codespaces → New secret (name + value).
Codespaces secrets are sealed per-repo; moving to another repo means re-adding them.

## Leak response

1. Rotate at the provider table above (immediate, takes seconds).
2. Re-add the new value to Codespaces secrets.
3. Audit recent runs for exfiltration (`gh api …/codespaces` activity).
4. Only then worry about git history — rotation first, always.
