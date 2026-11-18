# Roblox "In This World" story video: handoff

Give this file (and the zip it came in) to Claude on the new account and say:
"Read HANDOFF.md and continue the project from where it left off."

## Who and what

- Kalid is making viral Roblox "In this world / In this town" narrated story Shorts (TikTok, Reels, YouTube Shorts).
- Pipeline so far: Blender 5.3 (on the Windows desktop) builds and renders the animation; Claude adds captions, voice and sound effects with Python and ffmpeg.
- Kalid's preferences: no em dashes anywhere; direct, short, action-first answers; super simple steps when he has to do something. When using Roblox Studio or Blender through computer use, check if it is already open before launching it again. Never call save_place on a Studio place. Never type passwords; Kalid logs in himself. Ask before downloading files.

## Status (as of Nov 18, 2026)

1. Script 1 ("The balloons", 23 lines, about 1:45) is final. Full text and shot notes are in the playbook doc (export it as Markdown and include it, see below) and in `film/timing_s1.json` (`lines`).
2. Voice: ElevenLabs, voice "Adam - Dominant, Firm" (voice ID pNInz6obpgDQGcFmaJgB), model Multilingual v2. The final take is `film/adam/adam.mp3` (1:44.9). Kalid's ElevenLabs account is on the free plan.
3. v1 video is DONE: `balloons_full_v1.mp4` (540x960, 30 fps, 1:45). Adam audio sits at video frame 3 (2-frame delay) for best lip sync.
4. Kalid's review of v1: quality is low and the "architecture and setup looks off". He supplied a reference reel (bonk_films3, "In This Town, All the Girls Like the Same 3 Boys"). Comparison results are below. NEXT STEP is v2.

## Reference comparison (v1 vs reference)

| Metric | v1 | Reference |
|---|---|---|
| Resolution | 540x960, 1.2 Mbps | 1080x1920 |
| Edge/detail density | 0.035 | 0.090 (2.6x more texture and set dressing) |
| Cuts per 10 s | 3.1 | 6.8 |
| Median shot | 2.8 s | 1.3 s |
| Fully static frames | 19% | 1% |
| Blown-out whites | 2.9% | 0.3% |
| Colorfulness | 62 | 72 |
| Loudness | -16.4 LUFS | -14.4 LUFS |
| Silence | 24% of runtime | never (music bed throughout) |

Gaps, biggest first: plain primitive world vs a real textured Roblox town (half-timbered houses, cobblestone, lamps, bunting, crowds); flat lighting with no depth of field or contact shadows; camera too wide and static (reference is low, close, over-the-shoulder, foreground framing, plus top-down "diagram" shots with arrows and name tags); slow pacing; half resolution with low anti-aliasing; avatar textures less detailed; captions (reference: ONE word at a time, white with black outline, no color highlight; v1: 1 to 3 words with yellow key words); audio (reference has a music bed, louder and more compressed).

## Plan for v2 (proposed, Kalid had not yet confirmed)

1. Build the town, school and cliff sets and the cast in Roblox Studio from real Toolbox maps and real avatars (Studio MCP is installed on the desktop), export to Blender.
2. Render in Blender at 1080x1920, more EEVEE samples, depth of field, soft shadows/AO, AgX tone mapping, warm key light.
3. Re-cut to about 1.3 s median shots, constant subtle camera motion, add top-down diagram shots.
4. One-word white captions with black outline; add a quiet music bed; master to about -14 LUFS.
5. Keep the same script, Adam audio and timing map.

## Reference reel

`reference/bonk_films3_reference_screenrec.mp4` is Kalid's screen recording of the reference reel (Instagram UI included, downscaled to 646 wide). Re-run the comparison on any new render with:

```
ffmpeg -i reference/bonk_films3_reference_screenrec.mp4 -vf "fps=30,crop=iw*0.853:ih*0.64:0:ih*0.129" ref_crop.mp4
ffmpeg -i NEW.mp4 -vf "crop=iw*0.7:ih*0.64:iw*0.09:ih*0.13" new_crop.mp4
NW=378 python3 film/analyze.py ref_crop.mp4 ref ; NW=378 python3 film/analyze.py new_crop.mp4 new
```

Goal for v2: match or beat the reference column in the comparison table.

## Files in this bundle

- `film/`: caption/mix script (`caption_film.py`, usage: `python3 caption_film.py <frames_dir> <out.mp4> 30 cues_film_adam.json`, run from the film folder), cue files (`cues_film_adam.json` = 122 caption chunks + 54 SFX cues + Adam at frame 3), `timing_s1.json` (23 lines with start/end frames at 30 fps plus a mouth open/closed RLE for lip sync; Blender frame = timing index + 1), `adam/adam.mp3`, `sfx/` (original synthesized SFX), `analyze.py` (video metrics used for the comparison), `make_cues.py`.
- `blender_tools/`: every Blender script (`film_build.py` builds cast and sets, `film_shots6.py` is the verified final shot/animation script, `film_render*.py` render workers, `avatar.py`, `clothing.py`, `faces.py`, `expr3.py` expression system, `rbxt.py`, `run_bg2.py` background runner, etc.).
- `compare/`: comparison images and metrics JSON.
- `balloons_full_v1.mp4`: the finished v1.

## Desktop folder (NOT available: the old desktop is gone)

The old desktop will not be back, so `balloon_film.blend`, the face atlas PNGs and the rendered frames are lost. That is fine: v2 rebuilds the sets and cast from real Roblox assets anyway. Faces can be regenerated with `blender_tools/faces.py`, and the cast/clothing logic is in `avatar.py`, `clothing.py`, `rbxt.py`. Everything else (script, Adam audio, timing map, cues, SFX, caption pipeline) is in this repo. On the new desktop, create `Downloads\BalloonTest\tools` and copy `blender_tools/` into it so the old script paths still work.

### What the old folder contained (for reference)

`C:\Users\Kalid Ibrahim\Downloads\BalloonTest\` holds `balloon_film.blend` (final scene), `faces\` (face atlases faces4_<Name>.png), `sfx\`, `voice\`, `tools\` (same scripts as blender_tools), and `frames_film\` (3,164 rendered frames, optional). On a new desktop the scripts expect this same path under the new user's home, so keep the folder name `Downloads\BalloonTest`.

## How Claude drove Blender (tips)

- The Blender MCP never connected in the Claude app, so scripts were committed into `BalloonTest\tools` and run either by typing one line into Blender's Python console via computer use, or as background Blender processes: `subprocess.Popen([bpy.app.binary_path,'-b','--python',...])`.
- Python console context has no active_object; build meshes with bmesh, not bpy.ops primitives. Heavy scripts run in background mode (open_mainfile replaces the console area).
- Blender 5 layered actions: fcurves via `bpy_extras.anim_utils.action_get_channelbag_for_slot`.
- Committing the same file name to the desktop can deliver stale content; commit to a new file name and verify.
- In Blender menus, hover the item first, then press Enter (direct clicks sometimes don't register).
