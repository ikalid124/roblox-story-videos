# Chat history: Roblox story video project (Nov 14 to 18, 2026)

Condensed record of the original Claude chat. Kalid's messages are quoted word for word; Claude's work is summarized after each one. The earliest part of the chat (Blender MCP setup and tests v1 to v3) was already compacted inside the chat itself, so it is summarized only.

## Phase 1: setup and test renders v1 to v3 (Nov 14 to 15)

- Goal set: make viral Roblox "In this world" story Shorts using Blender and Claude on the Windows desktop (DESKTOP-B1F47GK), iterating tests until near perfect, then script and voice.
- Tried to connect the Blender MCP (`Setup Blender MCP.bat`, `setup-blender-mcp.ps1`). The MCP server inside Blender started (localhost:9876) but the Claude app's local "blender" MCP stayed in failed state, so Claude drove Blender by committing Python scripts to `Downloads\BalloonTest\tools` and running them through Blender's Python console (computer use) or as background Blender processes.
- Built Roblox-style avatars (`avatar.py`, `rbxt.py`, `clothing.py` with real Roblox clothing/hair asset IDs), a street set with houses, balloons, and test shots (test_v2_maya, test_v3_maya).
- Researched the trend (YouTube Shorts, 167 videos) and wrote the playbook doc (see PLAYBOOK.md).

## Phase 2: v4 and v5 tests (Nov 15 to 16)

> "Ok v4 time 1. Improvement I can see is her the black lady's lips are pink which doesn't match her pigment besides that the stories usually have a set of expressions rangin from sad to angry to really silly goofy and expressive and all the dif characters can change expressions this was just a demo but just making sure it's known. Besides that do your own analysis and improve upon you're design and also they all have the same voice and sound affects so we can start identifying those as well"

Claude built the expression system: a 6x4 face atlas per character (12 expressions plus a talking variant of each), skin-matched lips, projected on the head and switched by a keyed `expr` property; lip sync from the voice track; original synthesized SFX (boom, whoosh, sad wah, boing, sting, pop, ding, laugh hits); captions burned with PIL (Poppins Bold, 1 to 3 words, key words yellow). Result: test_v4.mp4.

> "Continue"

Next improvement round: test_v5.mp4.

> "Is the eleven labs free?"

Answered: free tier exists with monthly credits (Kalid's account: free plan, about 8,457 credits left at the time).

> "Try and use /agent-reach to research on tiktok and reels too but even if not lets work on our first script then i will give you adams voice then we can line it up wiht the animation"

Checked TikTok tag pages (same "In This World, [RULE IN CAPS]" packaging as YouTube; one compilation has a "You Can Only Say Sorr..." story to check). Wrote Script 1 final (23 lines, third person for one adult narrator) into the playbook.

> (screenshot of ElevenLabs plans) "how much credit will we probably need per video?"

About 1 credit per character on Multilingual v2 (0.5 on Flash). Script 1 is about 1,700 characters, so roughly 1,700 credits per take, plus retakes.

> (screenshot of a TikTok tutorial) "I see adam english and all the other stuff but i dont just see the adam they use"

> "do computer use"

> "Im not sure check both"

> "should be connected"

> "Yes, download it"

Claude found the original Adam ("Adam - Dominant, Firm", ID pNInz6obpgDQGcFmaJgB) in ElevenLabs via Claude in Chrome on the laptop and generated the full narration (1:44, in Kalid's ElevenLabs History, Generation 1).

> "Can you do desktop isntead"

> "I'm not at my desktop right now just transfer the data from my laptop to my desktop or something"

Claude extracted a frame-accurate timing map from the laptop page (`timing_s1.json`: 23 lines, mouth open/closed track at 30 fps) and moved it to the desktop.

> "go"

Claude built the full film in Blender: new cast (Teacher, Principal, Photographer, Dad, Kid3 plus Maya, Ezra, Grandpa, KidA, KidB), classroom, hallway and cliff sets (`film_build.py`), 33 shots with walks, expressions, lip sync, balloon physics-style sway, Ezra's 42-balloon flight and pops (`film_shots6.py`), rendered 3,164 frames at 540x960 with three parallel workers.

> "do you need the blender still?"

No; frames were rendered, Blender only needed again for re-renders.

> (uploaded the ElevenLabs Adam MP3)

Claude aligned the real Adam audio to the timing map (all 23 line starts within 0 to 4 frames; best lip-sync offset +2 frames) and built `cues_film_adam.json`.

> "Can the rest of it be done on this computer? without blender"

No; the frames lived only on the desktop.

> "ok desktop is back on"

Claude zipped the frames through Blender's console, pulled them over, burned captions, mixed Adam plus SFX and delivered `balloons_full_v1.mp4` (1:45, 540x960).

## Phase 3: review against a reference (Nov 18)

> "Yeah the quality is kind of bad on this but also the architecture and set up also looks off for example im going to uplaod a video of another video after this idk how you process videos but take screenshots do whatever to look at the quality and how the render looks and stuff and compare against a range of metrics and look at where my video falls short"

Kalid uploaded a screen recording of the bonk_films3 reel "In This Town, All the Girls Like the Same 3 Boys". Claude wrote `analyze.py` and compared. Findings (full table in HANDOFF.md): reference has 2.6x more detail (real textured Roblox town), cuts twice as often (median shot 1.3 s vs 2.8 s), almost never holds a still frame, uses depth of field and soft warm lighting, one-word white captions, a constant music bed, and is 1080x1920. Proposed v2: build sets and cast from real Roblox assets in Studio, export to Blender, render at full resolution with DOF and better lighting, re-cut faster, one-word captions, music bed, master to about -14 LUFS.

> "How can i continue on another claude account on a ntoher desktop without losing any progress at all?"

Claude made the handoff bundle (HANDOFF.md plus all files).

> "can you push it to git with litterally everything necessary maybe even a copy of this whole chat in there if possible"

This repo.

## Full raw transcript

The raw chat cannot be exported from inside the chat. To get it: on claude.ai, Settings, Privacy, Export data (exports all conversations from the first account as a download). Search the export for "BalloonTest" to find this chat.
