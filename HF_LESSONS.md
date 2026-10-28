# HyperFrames Production Lessons Learned

## Critical Rules (Section 7 + Section 8)

### 1. AUDIO DRIVES VISUALS — WORD TIMESTAMPS ARE TRUTH
- Extract word-level timestamps FIRST using Whisper (`assets/captions/words.json`)
- Scene boundaries MUST match narration topic transitions, NOT arbitrary time blocks
- If a word is spoken during a scene, its visual MUST appear in THAT scene
- Don't show next idea before current one is fully discussed

### 2. ELEMENT EXIT ANIMATIONS — THE GOLDEN RULE
**Every element that enters MUST exit before its scene ends.**

```javascript
// WRONG: Elements stay visible after scene ends, stacking up
tl.fromTo("#el", { opacity: 0 }, { opacity: 1 }, startTime);

// CORRECT: Reset elements before next scene
tl.fromTo("#el", { opacity: 0 }, { opacity: 1 }, startTime);
tl.set("#el", { opacity: 0 }, sceneEnd - 0.1);  // EXIT before scene ends
```

**Section 8 Failure**: We forgot exit animations. All 11 scenes' elements stacked on top of each other. Fixed by adding `tl.set()` reset at end of each scene.

**Section 7 Success**: Scenes had clear boundaries and HyperFrames framework handled visibility. But this was relying on framework behavior, not explicit animation control. Always add explicit exits.

### 3. SCENE BOUNDARY ALIGNMENT
Scene boundaries must align with narration transitions:
- Scene 1: "Let's actually build one" (0-4.66s)
- Scene 2: Tech stack cards (4.66-10.89s)  
- Scene 3: Empty folder (10.89-19.66s)
- Scene 4: AGENTS.md (19.66-31.73s)
- Scene 5: README.md (31.73-40.15s)
- Scene 6: ARCHITECTURE.md (40.15-55.65s)
- Scene 7: RULES.md (55.65-68.94s)
- Scene 8: STRUCTURE.md (68.94-79.46s)
- Scene 9: Two hours later (79.46-89.81s)
- Scene 10: AI demo (89.81-129.93s)
- Scene 11: Comparison (129.93-174s)

### 4. GSAP ANIMATION TIMING
- Visuals appear AS word is spoken (±0.3s tolerance)
- Duration: 0.3-0.5s for enter animations
- Ease: `power3.out` for slides, `back.out(1.5)` for scale-ups
- Use `fromTo` to prevent initial flash

### 5. NO STAGNANT SCREENS
- Visual changes every 2-3 seconds minimum
- Use staggered reveals for lists
- Each phrase gets its own dedicated animated frame
- Consider phrase-by-phrase animation (Section 7 approach)

### 6. WORKFLOW — MANDATORY ORDER
1. Extract word timestamps → `words.json`
2. Analyze timestamps → set scene boundaries at narration transitions
3. Design visuals → HTML structure with proper IDs
4. Animate with GSAP → synced to word timestamps, with EXIT animations
5. Verify sync → `hyperframes check`
6. Preview → `hyperframes preview --background`
7. User approval → get explicit OK
8. Render → `hyperframes render`

## Technical Details

### Contrast Requirements (WCAG AA)
- Minimum 4.5:1 contrast ratio for text
- Badge colors: use bright values (#93b8fc, #6ee7b7, #fcd34d)
- Text on dark: #e2e8f0 (light gray) or #94a3b8 (muted)
- Never use dark text on dark backgrounds

### Image Handling
- Background removal via `rembg` is slow (model downloads)
- Alternative: Use image backgrounds with dark overlays
- Filename case matters on some systems

### Process Management
- Kill `node`/`chrome*` processes between renders
- `hyperframes preview --stop` before render
- Check command: `hyperframes check`
- Render timeout: use 600000ms (10 min) for long sections

### Key Files
- `assets/captions/words.json` — Word-level timestamps
- `index.html` — Main composition with GSAP timeline
- `meta.json` — Section metadata
- `compositions/` — Sub-composition files (if split)

## Section-Specific Notes

### Section 7: Under the Hood
- 9 scenes, 111s duration
- Used image backgrounds with dark overlays (skipped bg removal)
- Phrase-by-phrase animation synced to timestamps
- Key lesson: Scene boundaries must match when goal words are spoken

### Section 8: Watching It Work
- 11 scenes, 174s duration (longest section)
- All phrase-by-phrase GSAP animations
- Fixed stacking issue by adding exit animations
- Key lesson: Every element needs explicit exit reset

### Section 9: Closing The Loop
- 8 scenes, 72.7s duration (shortest section)
- Clean phrase-by-phrase animation with EXIT animations
- Key lesson: Shorter sections benefit from tighter pacing
- Removed old composition files that caused font errors

## Common Mistakes to Avoid
1. Forgetting exit animations (elements stack up)
2. Scene boundaries not matching narration transitions
3. Dark text on dark backgrounds (contrast failure)
4. Not killing processes between renders
5. Not verifying with `hyperframes check` before preview
6. Showing next idea before current one is discussed
7. Old composition files in `compositions/` folder can cause errors
