# Section 7 (Under the Hood) - Lessons Learned

## Critical Principle: Audio Drives Visuals

**The narration determines what is shown, never the other way around.**

- Word-level timestamps from `assets/captions/words.json` are the source of truth
- Visuals must appear AS the word is spoken (within ±0.3s)
- Don't show the next idea before the current one is fully discussed
- If audio is still elaborating, stay with the current visual

---

## Scene Boundary Alignment

### The Problem
Scene boundaries in `data-start` / `data-duration` must align with when the narration transitions to a new topic, NOT when we think the topic starts.

### The Solution
1. Extract word timestamps for key transition phrases
2. Set scene boundaries at the exact moment the narration shifts
3. Example from Section 7:
   - "Scalable" spoken at 52.08s → Scene 6 starts at 52.0s
   - "Consistent" spoken at 60.81s → Scene 7 starts at 60.8s
   - "Same pattern" spoken at 76.21s → Scene 8 starts at 76.2s

### Rule
**If a word is spoken during a scene, the visual for that word must appear in THAT scene, not the next one.**

---

## Timing Analysis Workflow

### Step 1: Extract Word Timestamps
```python
import json
with open('assets/captions/words.json') as f:
    words = json.load(f)
```

### Step 2: Map Phrases to Timestamps
Find when each key phrase is spoken:
- Search for consecutive words matching the phrase
- Record start time of first word, end time of last word

### Step 3: Compare Animation vs Spoken Time
```
Animation Time - Spoken Time = Difference
- If difference > 0.3s → Animation is LATE
- If difference < -0.3s → Animation is EARLY
```

### Step 4: Adjust Animation Timing
Move GSAP `fromTo` calls to match spoken time exactly.

---

## GSAP Animation Patterns

### Basic Pattern
```javascript
tl.fromTo("#element", 
  { y: 20, opacity: 0 },           // Start state
  { y: 0, opacity: 1, duration: 0.4 },  // End state
  spokenTime  // When to start (matches word timestamp)
);
```

### Entrance Animations
- **Text**: `fromTo` with `y: 20` → `y: 0` (slide up)
- **Badges**: `fromTo` with `y: -20` → `y: 0` (drop down)
- **Dividers**: `fromTo` with `scaleX: 0` → `scaleX: 1` (grow)
- **Numbers**: `fromTo` with `scale: 3` → `scale: 1` (zoom in)

### Exit Animations
- Use `to` with `opacity: 0` before scene ends
- Or let the next scene's `data-start` hide the previous scene

---

## Common Pitfalls

### 1. Mismatched Scene Boundaries
**Problem**: Narration mentions a word during Scene X, but the visual appears in Scene X+1.

**Fix**: Adjust `data-start` and `data-duration` to match narration transitions.

### 2. Early Visual Appearance
**Problem**: Visual appears before the word is spoken (confuses viewer).

**Fix**: Set animation time to match spoken time, not earlier.

### 3. Late Visual Appearance
**Problem**: Visual appears after the word is spoken (feels disconnected).

**Fix**: Set animation time to match spoken time, or slightly before (0.1-0.2s early is OK).

### 4. Stagnant Screens
**Problem**: No visual change for 3+ seconds while narration continues.

**Fix**: Add intermediate animations or text reveals for each phrase.

---

## Verification Checklist

Before rendering, verify:

1. **Word-to-Visual Sync**: Every key word has a corresponding animation within ±0.3s
2. **Scene Boundaries**: Each scene starts/ends at narration transition points
3. **No Stagnant Screens**: Visual changes every 2-3 seconds minimum
4. **Contrast**: All text passes WCAG AA (4.5:1 for normal, 3:1 for large)
5. **Runtime Check**: `hyperframes check` passes with 0 errors

---

## Commands Reference

```bash
# Analysis
python scripts/analyze_timing.py  # Extract word timestamps

# Verification
hyperframes check .               # Lint + runtime + layout + motion + contrast

# Preview
hyperframes preview . --background  # Launch Studio preview
hyperframes preview . --stop        # Stop preview

# Render
hyperframes render .               # Render to MP4

# Pre-render cleanup
Get-Process -Name "node","chrome*" | Stop-Process -Force
```

---

## Section 7 Specific Notes

### Composition Structure
- 9 scenes total (Intro, 40 Rules, Four Goals, Predictable, Modular, Scalable, Consistent, Same Pattern, Worth It)
- Total duration: 111.1 seconds
- 3333 frames at 30fps

### Key Timing Points
| Scene | Start | End | Key Phrase |
|-------|-------|-----|------------|
| 1 | 0.0s | 4.312s | "Now let's go a little deeper" |
| 2 | 4.312s | 14.312s | "40 small rules" |
| 3 | 14.312s | 24.312s | "four goals" |
| 4 | 24.312s | 38.312s | "Predictable" |
| 5 | 38.312s | 52.0s | "Modular" |
| 6 | 52.0s | 60.8s | "Scalable" |
| 7 | 60.8s | 76.2s | "Consistent" |
| 8 | 76.2s | 90.3s | "Same pattern" |
| 9 | 90.3s | 111.1s | "Worth it" |

### Render Output
- File: `C:\Users\user\renders\agent-ready-under-the-hood_2026-09-03_15-37-57.mp4`
- Size: 7.6 MB
- Duration: 1m 51.1s
- Render time: 3m 20.3s

---

## Application to Next Section

When building the next section:

1. **Start with word timestamps** - Extract all words before designing visuals
2. **Map narration flow** - Identify when topics transition
3. **Set scene boundaries first** - Align with narration, not arbitrary time blocks
4. **Design visuals second** - What to show based on what's being said
5. **Animate third** - Timing based on word timestamps
6. **Verify fourth** - Check sync, contrast, runtime
7. **Preview fifth** - Get user approval
8. **Render last** - After all checks pass
