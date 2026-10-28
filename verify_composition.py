#!/usr/bin/env python3
"""
HyperFrames Composition Verifier
Runs automated checks for: overlaps, sync issues, blank gaps, element positioning.
Must be run BEFORE presenting any composition to the user.

Usage:
    python verify_composition.py <project_dir>
"""

import json
import re
import sys
import os
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from pathlib import Path

@dataclass
class Element:
    id: str
    scene: str
    x_pct: float = 0.0
    y_pct: float = 0.0
    width_px: float = 0.0
    height_px: float = 0.0
    x_translate: float = 0.0
    y_translate: float = 0.0
    font_size: int = 0
    text: str = ""
    start_time: float = 0.0
    end_time: float = 0.0
    
    @property
    def center_x(self) -> float:
        base_x = (self.x_pct / 100.0) * 1920.0
        if self.x_translate == -50:
            return base_x
        return base_x + self.x_translate
    
    @property
    def center_y(self) -> float:
        base_y = (self.y_pct / 100.0) * 1080.0
        if self.y_translate == -50:
            return base_y
        return base_y + self.y_translate
    
    @property
    def left(self) -> float:
        return self.center_x - (self.width_px / 2.0)
    
    @property
    def right(self) -> float:
        return self.center_x + (self.width_px / 2.0)
    
    @property
    def top(self) -> float:
        return self.center_y - (self.height_px / 2.0)
    
    @property
    def bottom(self) -> float:
        return self.center_y + (self.height_px / 2.0)

@dataclass
class Word:
    id: str
    text: str
    start: float
    end: float

@dataclass
class Issue:
    severity: str
    category: str
    scene: str
    message: str
    element_a: str = ""
    element_b: str = ""
    fix: str = ""

def parse_words_json(filepath: str) -> List[Word]:
    with open(filepath, 'r') as f:
        data = json.load(f)
    return [Word(id=w['id'], text=w['text'], start=w['start'], end=w['end']) for w in data]

def estimate_text_size(text: str, font_size: int) -> Tuple[float, float]:
    char_count = len(text)
    width = char_count * font_size * 0.55
    height = font_size * 1.2
    return width, height

def parse_index_html(filepath: str) -> Tuple[List[Element], List[dict]]:
    """Parse index.html line by line to find all elements."""
    elements = []
    scenes = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    full_content = ''.join(lines)
    
    # Find scenes - handle data-hf-id before or after id
    scene_pattern = re.compile(r'id="(scene-\d+)"[^>]*?data-start="([\d.]+)"[^>]*?data-duration="([\d.]+)"')
    scenes = []
    for match in scene_pattern.finditer(full_content):
        scenes.append({
            'id': match.group(1),
            'start': float(match.group(2)),
            'duration': float(match.group(3)),
            'end': float(match.group(2)) + float(match.group(3))
        })
    
    # Find elements by scanning lines for id="s\d+-..."
    elem_ids_found = set()
    
    for i, line in enumerate(lines):
        # Look for div elements with id starting with s\d+-
        id_match = re.search(r'id="(s\d+-[^"]+)"', line)
        if not id_match:
            continue
        
        elem_id = id_match.group(1)
        if elem_id in elem_ids_found:
            continue
        elem_ids_found.add(elem_id)
        
        # Get full line (may span multiple lines for style)
        # Collect lines until we find the closing > of the opening tag
        full_line = line
        j = i + 1
        # Count opening and closing divs to handle nesting
        open_divs = full_line.count('<div')
        close_divs = full_line.count('</div>')
        while j < len(lines) and open_divs > close_divs:
            full_line += ' ' + lines[j]
            open_divs += lines[j].count('<div')
            close_divs += lines[j].count('</div>')
            j += 1
        
        # Extract style - only from the opening tag, not from nested elements
        # Find the style in the opening div tag only
        opening_tag_match = re.search(r'<div[^>]*style="([^"]*)"', full_line, re.DOTALL)
        if not opening_tag_match:
            continue  # Skip elements without inline styles (nested in containers)
        style = opening_tag_match.group(1)
        
        # Debug: print what we found
        if 'rule' in elem_id:
            print(f"DEBUG: {elem_id} - full_line length: {len(full_line)}")
            try:
                print(f"DEBUG: {elem_id} - first 200 chars: {full_line[:200]}")
            except UnicodeEncodeError:
                print(f"DEBUG: {elem_id} - first 200 chars: {full_line[:200].encode('ascii', 'ignore').decode()}")
        
        # Extract text content between > and </div>
        text_match = re.search(r'>([^<]*)</div>', full_line, re.DOTALL)
        text_content = text_match.group(1).strip() if text_match else ""
        
        # Determine scene
        scene_num_match = re.match(r's(\d+)-', elem_id)
        if not scene_num_match:
            continue
        scene_num = scene_num_match.group(1).zfill(2)  # Pad with leading zero
        scene_info = next((s for s in scenes if s['id'] == f'scene-{scene_num}'), None)
        if not scene_info:
            continue
        
        elem = Element(
            id=elem_id,
            scene=scene_info['id'],
            text=text_content,
            start_time=scene_info['start'],
            end_time=scene_info['end']
        )
        
        # Parse position
        left_match = re.search(r'left:\s*([\d.]+)%', style)
        if left_match:
            elem.x_pct = float(left_match.group(1))
        
        top_match = re.search(r'top:\s*([\d.]+)%', style)
        if top_match:
            elem.y_pct = float(top_match.group(1))
        
        font_match = re.search(r'font-size:\s*(\d+)px', style)
        if font_match:
            elem.font_size = int(font_match.group(1))
        
        # Check translate
        if 'translate(-50%, -50%)' in style:
            elem.x_translate = -50
            elem.y_translate = -50
        
        translate_match = re.search(r'translate\(([-\d.]+)px,\s*([-\d.]+)px\)', style)
        if translate_match:
            elem.x_translate += float(translate_match.group(1))
            elem.y_translate += float(translate_match.group(2))
        
        # Estimate size
        if text_content and elem.font_size > 0:
            elem.width_px, elem.height_px = estimate_text_size(text_content, elem.font_size)
        elif elem.font_size > 0:
            elem.width_px = elem.font_size * 1.5
            elem.height_px = elem.font_size * 1.5
        else:
            elem.width_px = 200
            elem.height_px = 60
        
        elements.append(elem)
    
    return elements, scenes

def check_overlaps(elements: List[Element]) -> List[Issue]:
    issues = []
    
    for i, elem_a in enumerate(elements):
        for elem_b in elements[i+1:]:
            if elem_a.scene != elem_b.scene:
                continue
            
            # Skip elements at default position (inside containers)
            if elem_a.left <= 0 and elem_a.top <= 0:
                continue
            if elem_b.left <= 0 and elem_b.top <= 0:
                continue
            
            # Check position overlap
            x_overlap = (elem_a.left < elem_b.right and elem_a.right > elem_b.left)
            y_overlap = (elem_a.top < elem_b.bottom and elem_a.bottom > elem_b.top)
            
            if x_overlap and y_overlap:
                overlap_x = min(elem_a.right, elem_b.right) - max(elem_a.left, elem_b.left)
                overlap_y = min(elem_a.bottom, elem_b.bottom) - max(elem_a.top, elem_b.top)
                
                # Only report if overlap is significant (> 10px in both dimensions)
                if overlap_x > 10 and overlap_y > 10:
                    issues.append(Issue(
                        severity="ERROR",
                        category="OVERLAP",
                        scene=elem_a.scene,
                        message=(
                            f"OVERLAP: '{elem_a.id}' and '{elem_b.id}'\n"
                            f"  {elem_a.id}: pos=({elem_a.left:.0f},{elem_a.top:.0f}) size=({elem_a.width_px:.0f}x{elem_a.height_px:.0f})\n"
                            f"  {elem_b.id}: pos=({elem_b.left:.0f},{elem_b.top:.0f}) size=({elem_b.width_px:.0f}x{elem_b.height_px:.0f})\n"
                            f"  Overlap: {overlap_x:.0f}px x {overlap_y:.0f}px"
                        ),
                        element_a=elem_a.id,
                        element_b=elem_b.id
                    ))
    
    return issues

def check_sizes(elements: List[Element]) -> List[Issue]:
    """Check for elements that are too small for mobile viewing."""
    issues = []
    
    for elem in elements:
        # Skip elements at default position (inside containers)
        if elem.left <= 0 and elem.top <= 0:
            continue
        
        # Check font size (text elements)
        if elem.text and elem.font_size > 0:
            if elem.font_size < 20:
                issues.append(Issue(
                    severity="WARNING",
                    category="SIZE",
                    scene=elem.scene,
                    message=(
                        f"TEXT TOO SMALL: '{elem.id}' has font-size: {elem.font_size}px\n"
                        f"  Minimum recommended: 20px for mobile viewing\n"
                        f"  Text: '{elem.text[:30]}'"
                    ),
                    element_a=elem.id
                ))
        
        # Check overall element size
        if elem.width_px > 0 and elem.height_px > 0:
            # Text elements should be at least 100px wide
            if elem.text and elem.width_px < 100:
                issues.append(Issue(
                    severity="WARNING",
                    category="SIZE",
                    scene=elem.scene,
                    message=(
                        f"ELEMENT TOO NARROW: '{elem.id}' is {elem.width_px:.0f}px wide\n"
                        f"  Minimum recommended: 100px for readability\n"
                    ),
                    element_a=elem.id
                ))
            
            # Elements should be at least 30px tall
            if elem.height_px < 30:
                issues.append(Issue(
                    severity="WARNING",
                    category="SIZE",
                    scene=elem.scene,
                    message=(
                        f"ELEMENT TOO SHORT: '{elem.id}' is {elem.height_px:.0f}px tall\n"
                        f"  Minimum recommended: 30px for visibility\n"
                    ),
                    element_a=elem.id
                ))
        
        # Check if element is too close to edge (less than 5% margin)
        margin = 0.05
        if elem.x_pct < margin * 100:
            issues.append(Issue(
                severity="WARNING",
                category="POSITION",
                scene=elem.scene,
                message=(
                    f"TOO CLOSE TO LEFT EDGE: '{elem.id}' at {elem.x_pct:.1f}%\n"
                    f"  Minimum recommended: {margin*100:.0f}% margin\n"
                ),
                element_a=elem.id
            ))
        if elem.x_pct > (1 - margin) * 100:
            issues.append(Issue(
                severity="WARNING",
                category="POSITION",
                scene=elem.scene,
                message=(
                    f"TOO CLOSE TO RIGHT EDGE: '{elem.id}' at {elem.x_pct:.1f}%\n"
                    f"  Maximum recommended: {(1-margin)*100:.0f}% margin\n"
                ),
                element_a=elem.id
            ))
        if elem.y_pct < margin * 100:
            issues.append(Issue(
                severity="WARNING",
                category="POSITION",
                scene=elem.scene,
                message=(
                    f"TOO CLOSE TO TOP EDGE: '{elem.id}' at {elem.y_pct:.1f}%\n"
                    f"  Minimum recommended: {margin*100:.0f}% margin\n"
                ),
                element_a=elem.id
            ))
        if elem.y_pct > (1 - margin) * 100:
            issues.append(Issue(
                severity="WARNING",
                category="POSITION",
                scene=elem.scene,
                message=(
                    f"TOO CLOSE TO BOTTOM EDGE: '{elem.id}' at {elem.y_pct:.1f}%\n"
                    f"  Maximum recommended: {(1-margin)*100:.0f}% margin\n"
                ),
                element_a=elem.id
            ))
    
    return issues

def check_gaps(elements: List[Element], scenes: List[dict], words: List[Word]) -> List[Issue]:
    issues = []
    
    for scene in scenes:
        scene_elements = [e for e in elements if e.scene == scene['id']]
        scene_words = [w for w in words if w.start >= scene['start'] and w.start < scene['end']]
        
        if not scene_words or not scene_elements:
            continue
        
        # Check if first word has a visual within 1 second
        first_word = scene_words[0]
        first_visual = min(scene_elements, key=lambda e: e.start_time)
        
        if first_visual.start_time - first_word.start > 1.0:
            issues.append(Issue(
                severity="WARNING",
                category="GAP",
                scene=scene['id'],
                message=(
                    f"GAP: No visual for first {first_visual.start_time - first_word.start:.1f}s of scene\n"
                    f"  First word: '{first_word.text}' at {first_word.start:.2f}s\n"
                    f"  First visual: '{first_visual.id}' at {first_visual.start_time:.2f}s"
                )
            ))
    
    return issues

def generate_word_timing_report(elements: List[Element], scenes: List[dict], words: List[Word], project_dir: str):
    """Generate a word-timing sync report for manual verification."""
    
    # Parse GSAP timeline to get actual element animation times
    index_path = os.path.join(project_dir, 'index.html')
    element_anim_times = parse_gsap_timeline(index_path)
    
    # Group words by scene
    scene_words = {}
    for word in words:
        for scene in scenes:
            if scene['start'] <= word.start < scene['end']:
                if scene['id'] not in scene_words:
                    scene_words[scene['id']] = []
                scene_words[scene['id']].append(word)
                break
    
    # Generate report
    report_lines = []
    report_lines.append("# Word-Timing Sync Verification Report")
    report_lines.append(f"\nGenerated from: {project_dir}")
    report_lines.append(f"Total words: {len(words)}")
    report_lines.append(f"Total scenes: {len(scenes)}")
    report_lines.append("")
    
    # Track sync issues
    sync_issues = []
    
    for scene in scenes:
        scene_id = scene['id']
        s_words = scene_words.get(scene_id, [])
        scene_elements = [e for e in elements if e.scene == scene_id]
        
        report_lines.append(f"\n## {scene_id} ({scene['start']:.1f}s - {scene['end']:.1f}s)")
        report_lines.append(f"Duration: {scene['duration']:.1f}s")
        report_lines.append(f"Words: {len(s_words)}")
        report_lines.append(f"Visual elements: {len(scene_elements)}")
        
        # Words table
        report_lines.append("\n### Words Spoken")
        report_lines.append("| # | Word | Start | End | Duration |")
        report_lines.append("|---|------|-------|-----|----------|")
        for i, word in enumerate(s_words, 1):
            duration = word.end - word.start
            report_lines.append(f"| {i} | {word.text} | {word.start:.2f}s | {word.end:.2f}s | {duration:.3f}s |")
        
        # Visual elements table with actual animation times
        report_lines.append("\n### Visual Elements Shown")
        report_lines.append("| # | Element | Anim Start | Position | Size | Text |")
        report_lines.append("|---|---------|------------|----------|------|------|")
        for i, elem in enumerate(scene_elements, 1):
            anim_time = element_anim_times.get(elem.id, elem.start_time)
            pos = f"({elem.x_pct:.0f}%, {elem.y_pct:.0f}%)"
            size = f"{elem.width_px:.0f}x{elem.height_px:.0f}"
            text = elem.text[:30] if elem.text else "(no text)"
            report_lines.append(f"| {i} | {elem.id} | {anim_time:.2f}s | {pos} | {size} | {text} |")
        
        # Automated sync check
        report_lines.append("\n### Automated Sync Check")
        report_lines.append("Checking if each word has a corresponding visual...")
        report_lines.append("")
        
        for word in s_words:
            # Find visual elements that are visible when this word is spoken
            # A visual is visible if it animates in BEFORE or DURING the word
            matching_visuals = []
            for elem in scene_elements:
                anim_time = element_anim_times.get(elem.id, elem.start_time)
                # Visual is visible if it appears before or during the word (within +0.5s)
                # and the word starts after the visual appears or within 1s after
                if anim_time <= word.start + 0.5:
                    matching_visuals.append(elem.id)
            
            status = "OK" if matching_visuals else "MISSING"
            visuals_str = ", ".join(matching_visuals) if matching_visuals else "(none)"
            
            if not matching_visuals:
                sync_issues.append({
                    'scene': scene_id,
                    'word': word.text,
                    'time': word.start,
                    'issue': 'No visual element found'
                })
            
            report_lines.append(f"- **{word.text}** at {word.start:.2f}s: {status} → {visuals_str}")
        
        report_lines.append("")
    
    # Write report to file
    report_path = os.path.join(project_dir, 'SYNC_VERIFICATION_REPORT.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    
    print(f"\nReport generated: {report_path}")
    
    # Print sync issues summary
    if sync_issues:
        print(f"\n{'='*70}")
        print("SYNC ISSUES FOUND")
        print(f"{'='*70}")
        for issue in sync_issues:
            print(f"  {issue['scene']}: '{issue['word']}' at {issue['time']:.2f}s - {issue['issue']}")
        print(f"\nTotal issues: {len(sync_issues)}")
    else:
        print(f"\n{'='*70}")
        print("ALL WORDS HAVE CORRESPONDING VISUALS")
        print(f"{'='*70}")
    
    # Print summary to console
    print("\n" + "-" * 70)
    print("SCENE WORD COUNTS")
    print("-" * 70)
    for scene in scenes:
        s_words = scene_words.get(scene['id'], [])
        word_texts = [w.text for w in s_words[:5]]
        preview = " ".join(word_texts) + ("..." if len(s_words) > 5 else "")
        print(f"  {scene['id']}: {len(s_words)} words - \"{preview}\"")

def parse_gsap_timeline(index_path: str) -> dict:
    """Parse GSAP timeline to get actual element animation start times."""
    element_times = {}
    
    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find GSAP timeline animations
    # Pattern: tl.fromTo('#element-id', {...}, {...}, TIMESTAMP)
    # The timestamp is the last parameter before the closing )
    
    # Match tl.fromTo with nested braces
    pattern_fromto = r"tl\.fromTo\('#([^']+)',\s*\{[^{}]*\},\s*\{[^{}]*\},\s*([\d.]+)\)"
    for match in re.finditer(pattern_fromto, content):
        elem_id = match.group(1)
        anim_time = float(match.group(2))
        if elem_id not in element_times or anim_time < element_times[elem_id]:
            element_times[elem_id] = anim_time
    
    # Match tl.to with nested braces
    pattern_to = r"tl\.to\('#([^']+)',\s*\{[^{}]*\},\s*([\d.]+)\)"
    for match in re.finditer(pattern_to, content):
        elem_id = match.group(1)
        anim_time = float(match.group(2))
        if elem_id not in element_times or anim_time < element_times[elem_id]:
            element_times[elem_id] = anim_time
    
    # Match tl.set
    pattern_set = r"tl\.set\('#([^']+)',\s*\{[^{}]*\},\s*([\d.]+)\)"
    for match in re.finditer(pattern_set, content):
        elem_id = match.group(1)
        anim_time = float(match.group(2))
        if elem_id not in element_times or anim_time < element_times[elem_id]:
            element_times[elem_id] = anim_time
    
    return element_times

def parse_gsap_animation_events(index_path: str) -> list:
    """Parse GSAP timeline to extract ALL animation events with their timestamps.
    Returns list of (timestamp, element_id, event_type) tuples.
    Also detects repeat:-1 animations as continuous visual changes."""
    events = []
    
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        return events
    
    # Match tl.fromTo animations
    pattern_fromto = r"tl\.fromTo\('#([^']+)',\s*\{[^{}]*\},\s*\{[^{}]*\},\s*([\d.]+)\)"
    for match in re.finditer(pattern_fromto, content):
        events.append((float(match.group(2)), match.group(1), 'fromTo'))
    
    # Match tl.to animations
    pattern_to = r"tl\.to\('#([^']+)',\s*\{[^{}]*\},\s*([\d.]+)\)"
    for match in re.finditer(pattern_to, content):
        events.append((float(match.group(2)), match.group(1), 'to'))
    
    # Match tl.set
    pattern_set = r"tl\.set\('#([^']+)',\s*\{[^{}]*\},\s*([\d.]+)\)"
    for match in re.finditer(pattern_set, content):
        events.append((float(match.group(2)), match.group(1), 'set'))
    
    # Detect repeat:-1 animations and add multiple change points
    # These animations run continuously, so they prevent stagnation
    repeat_pattern = r"tl\.to\('#([^']+)',\s*\{[^{}]*repeat:\s*-1[^{}]*\},\s*([\d.]+)\)"
    for match in re.finditer(repeat_pattern, content):
        elem_id = match.group(1)
        start_time = float(match.group(2))
        # Add change points every 2 seconds for repeat:-1 animations
        for t in range(0, 30, 2):
            events.append((start_time + t, f"{elem_id}/repeat", 'continuous'))
    
    # Sort by timestamp
    events.sort(key=lambda x: x[0])
    return events

def parse_subcomposition_refs(index_path: str) -> list:
    """Parse index.html to find sub-composition file references."""
    refs = []
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        return refs
    
    # Match data-composition-src="compositions/scene-XX.html"
    pattern = r'data-composition-src="([^"]+)"'
    for match in re.finditer(pattern, content):
        refs.append(match.group(1))
    
    return refs

def check_stagnant_screens(index_path: str, scenes: list) -> list:
    """Check for periods where no visual changes occur for >2.5 seconds.
    This is critical for maintaining viewer attention."""
    issues = []
    
    # Parse main composition
    all_events = parse_gsap_animation_events(index_path)
    
    # Parse sub-compositions
    sub_comp_refs = parse_subcomposition_refs(index_path)
    project_dir = os.path.dirname(index_path)
    for ref in sub_comp_refs:
        sub_path = os.path.join(project_dir, ref)
        sub_events = parse_gsap_animation_events(sub_path)
        # Offset sub-comp events by scene start time
        # Extract scene number from filename
        scene_match = re.search(r'scene-(\d+)', ref)
        if scene_match:
            scene_num = int(scene_match.group(1))
            # Find corresponding scene in scenes list
            scene_info = next((s for s in scenes if s['id'] == f'scene-{scene_num:02d}'), None)
            if scene_info:
                offset = scene_info['start']
                for ts, elem_id, event_type in sub_events:
                    all_events.append((ts + offset, f"scene-{scene_num:02d}/{elem_id}", event_type))
    
    # Sort all events by timestamp
    all_events.sort(key=lambda x: x[0])
    
    if not all_events and not scenes:
        return issues
    
    if not scenes:
        return issues
    
    total_start = min(s['start'] for s in scenes)
    total_end = max(s['end'] for s in scenes)
    
    # Create a timeline of visual change events
    change_points = [total_start]
    for ts, elem_id, event_type in all_events:
        if total_start <= ts <= total_end:
            change_points.append(ts)
    change_points.append(total_end)
    
    # Remove duplicates and sort
    change_points = sorted(set(change_points))
    
    # Check for gaps > 2.5 seconds between visual changes
    MAX_STAGNATION = 2.5  # seconds
    
    for i in range(len(change_points) - 1):
        gap_duration = change_points[i + 1] - change_points[i]
        if gap_duration > MAX_STAGNATION:
            gap_start = change_points[i]
            gap_end = change_points[i + 1]
            
            issues.append({
                'severity': 'WARNING',
                'type': 'STAGNANT_SCREEN',
                'message': f"No visual change for {gap_duration:.1f}s (from {gap_start:.2f}s to {gap_end:.2f}s) — max allowed is {MAX_STAGNATION}s",
                'fix': "Add subtle animation (pulse, glow, camera drift) or introduce new element to maintain visual interest",
                'time_range': (gap_start, gap_end)
            })
    
    return issues

def check_progressive_disclosure(index_path: str, scenes: list) -> list:
    """Check for progressive disclosure issues:
    - Multiple elements appearing at the same time (should be staggered)
    - Elements that appear without proper entrance animation
    - Charts/diagrams that appear all at once instead of building progressively
    """
    issues = []
    
    # Parse all animation events
    all_events = parse_gsap_animation_events(index_path)
    
    # Parse sub-compositions
    sub_comp_refs = parse_subcomposition_refs(index_path)
    project_dir = os.path.dirname(index_path)
    for ref in sub_comp_refs:
        sub_path = os.path.join(project_dir, ref)
        sub_events = parse_gsap_animation_events(sub_path)
        scene_match = re.search(r'scene-(\d+)', ref)
        if scene_match:
            scene_num = int(scene_match.group(1))
            scene_info = next((s for s in scenes if s['id'] == f'scene-{scene_num:02d}'), None)
            if scene_info:
                offset = scene_info['start']
                for ts, elem_id, event_type in sub_events:
                    all_events.append((ts + offset, f"scene-{scene_num:02d}/{elem_id}", event_type))
    
    all_events.sort(key=lambda x: x[0])
    
    if not all_events:
        return issues
    
    # Check for multiple elements appearing within 0.1 seconds (should be staggered)
    # Exclude 'continuous' events from this check
    MIN_STAGGER = 0.15  # seconds between element entrances
    
    i = 0
    while i < len(all_events) - 1:
        current_ts = all_events[i][0]
        # Only check non-continuous events
        if all_events[i][2] != 'continuous':
            cluster = [all_events[i]]
            
            # Find all events within MIN_STAGGER seconds (excluding continuous)
            j = i + 1
            while j < len(all_events) and all_events[j][0] - current_ts <= MIN_STAGGER:
                if all_events[j][2] != 'continuous':
                    cluster.append(all_events[j])
                j += 1
            
            # If 3+ non-continuous elements appear at almost the same time, it's a disclosure issue
            if len(cluster) >= 3:
                elem_names = [e[1].split('/')[-1] for e in cluster]
                issues.append({
                    'severity': 'WARNING',
                    'type': 'PROGRESSIVE_DISCLOSURE',
                    'message': f"{len(cluster)} elements appear simultaneously at {current_ts:.2f}s: {', '.join(elem_names[:5])}{'...' if len(elem_names) > 5 else ''}",
                    'fix': "Stagger element entrances by 0.15-0.3s each. Show one idea at a time as narration mentions it.",
                    'time_range': (current_ts, current_ts)
                })
        
        i += 1
    
    return issues

def verify_composition(project_dir: str) -> bool:
    print("=" * 70)
    print("HYPERFRAMES COMPOSITION VERIFIER")
    print("=" * 70)
    print(f"\nProject: {project_dir}")
    
    index_path = os.path.join(project_dir, 'index.html')
    words_path = os.path.join(project_dir, 'assets', 'captions', 'words.json')
    
    if not os.path.exists(index_path):
        print(f"\n[ERROR] index.html not found")
        return False
    
    words = []
    if os.path.exists(words_path):
        words = parse_words_json(words_path)
        print(f"Loaded {len(words)} words from transcript")
    
    print("\nParsing composition...")
    elements, scenes = parse_index_html(index_path)
    print(f"Found {len(elements)} elements across {len(scenes)} scenes")
    
    # Print scene summary
    print("\n" + "-" * 70)
    print("SCENE SUMMARY")
    print("-" * 70)
    for scene in scenes:
        scene_elems = [e for e in elements if e.scene == scene['id']]
        print(f"  {scene['id']}: {scene['start']:.1f}s - {scene['end']:.1f}s ({scene['duration']:.1f}s) [{len(scene_elems)} elements]")
    
    # Print element details
    print("\n" + "-" * 70)
    print("ELEMENT DETAILS")
    print("-" * 70)
    for elem in sorted(elements, key=lambda e: (e.scene, e.start_time)):
        print(f"\n  {elem.id} ({elem.scene})")
        print(f"    Position: left={elem.x_pct:.1f}% top={elem.y_pct:.1f}%")
        print(f"    Bounds: ({elem.left:.0f},{elem.top:.0f}) to ({elem.right:.0f},{elem.bottom:.0f})")
        print(f"    Size: {elem.width_px:.0f}x{elem.height_px:.0f}px")
        if elem.text:
            try:
                print(f"    Text: '{elem.text[:50]}'")
            except UnicodeEncodeError:
                print(f"    Text: '{elem.text[:50].encode('ascii', 'ignore').decode()}'")
    
    # Run checks
    all_issues = []
    
    print("\n" + "-" * 70)
    print("CHECKING FOR OVERLAPS...")
    print("-" * 70)
    overlap_issues = check_overlaps(elements)
    all_issues.extend(overlap_issues)
    if overlap_issues:
        for issue in overlap_issues:
            print(f"\n  [ERROR] {issue.message}")
    else:
        print("  No overlaps found")
    
    print("\n" + "-" * 70)
    print("CHECKING FOR SIZES...")
    print("-" * 70)
    size_issues = check_sizes(elements)
    all_issues.extend(size_issues)
    if size_issues:
        for issue in size_issues:
            print(f"\n  [WARNING] {issue.message}")
    else:
        print("  All sizes OK")
    
    print("\n" + "-" * 70)
    print("CHECKING FOR GAPS...")
    print("-" * 70)
    gap_issues = check_gaps(elements, scenes, words)
    all_issues.extend(gap_issues)
    if gap_issues:
        for issue in gap_issues:
            print(f"\n  [WARNING] {issue.message}")
    else:
        print("  No gaps found")
    
    print("\n" + "-" * 70)
    print("CHECKING FOR STAGNANT SCREENS...")
    print("-" * 70)
    stagnant_issues = check_stagnant_screens(index_path, scenes)
    all_issues.extend([Issue(severity=i['severity'], category=i['type'], scene='all', message=i['message'], fix=i['fix']) for i in stagnant_issues])
    if stagnant_issues:
        for issue in stagnant_issues:
            print(f"\n  [{issue['severity']}] {issue['message']}")
            print(f"    Fix: {issue['fix']}")
    else:
        print("  No stagnant screens found — visual changes occur frequently enough")
    
    print("\n" + "-" * 70)
    print("CHECKING FOR PROGRESSIVE DISCLOSURE ISSUES...")
    print("-" * 70)
    disclosure_issues = check_progressive_disclosure(index_path, scenes)
    all_issues.extend([Issue(severity=i['severity'], category=i['type'], scene='all', message=i['message'], fix=i['fix']) for i in disclosure_issues])
    if disclosure_issues:
        for issue in disclosure_issues:
            print(f"\n  [{issue['severity']}] {issue['message']}")
            print(f"    Fix: {issue['fix']}")
    else:
        print("  No progressive disclosure issues — elements are properly staggered")
    
    # Summary
    errors = [i for i in all_issues if i.severity == "ERROR"]
    warnings = [i for i in all_issues if i.severity == "WARNING"]
    
    print("\n" + "=" * 70)
    print(f"RESULT: {len(errors)} errors, {len(warnings)} warnings")
    if errors:
        print("MUST FIX BEFORE PRESENTING")
    elif warnings:
        print("REVIEW BEFORE RENDERING")
    else:
        print("ALL CHECKS PASSED")
    print("=" * 70)
    
    # Generate word-timing sync report
    print("\n" + "=" * 70)
    print("WORD-TIMING SYNC REPORT")
    print("=" * 70)
    generate_word_timing_report(elements, scenes, words, project_dir)
    
    return len(errors) == 0

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python verify_composition.py <project_dir>")
        sys.exit(1)
    
    project_dir = sys.argv[1]
    if not os.path.isdir(project_dir):
        print(f"Error: Directory not found: {project_dir}")
        sys.exit(1)
    
    success = verify_composition(project_dir)
    sys.exit(0 if success else 1)
