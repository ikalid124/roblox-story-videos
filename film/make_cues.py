import json
T = json.load(open('timing_s1.json')); N = T['frames']
mask = []; v = 0
for r in T['mouth_rle']: mask += [v] * r; v ^= 1
CH = {
1: ["In this world,", "every *sorry*", "you owe", "becomes a *balloon*", "tied to", "your wrist."],
2: ["Say *sorry,*", "and it *pops.*"],
3: ["Most people carry", "*two or three.*", "Grandpa Joe", "carries *eleven,*", "so he ties", "himself to", "the *mailbox*", "at night."],
4: ["The *principal*", "wears", "*ankle weights.*"],
5: ["On picture day,", "the photographer", "stands on", "a *ladder.*"],
6: ["And if you", "ever *float?*", "Everyone knows", "what that means.", "You're a", "*bad person.*"],
7: ["*Maya*", "has had", "*one* balloon", "since she", "was six.", "*Gray.*", "It never pops.", "No matter who", "she says", "*sorry* to."],
8: ["Then there's *Ezra.*", "*Forty-two* balloons.", "He *floats*", "to school."],
9: ["Kids throw paper", "at him", "from the", "second floor.", "The teacher", "ties him", "to the *radiator.*"],
10: ["Even Maya", "called him", "a *bully.*", "She'd never", "even talked", "to him."],
11: ["Then, on", "the field trip", "to the *cliffs,*", "the wind", "picked up...", "and Ezra's rope", "*snapped.*"],
12: ["He shot", "straight up,", "over the edge,", "toward the *ocean.*"],
13: ["Everyone screamed,", "\"Say *sorry,* Ezra!", "*Pop them!*\""],
14: ["\"I've tried!", "Every single day!", "They *don't pop!*\""],
15: ["That's when Maya", "looked up", "at her", "*gray balloon.*", "Six years.", "*Never popped.*"],
16: ["Because her *dad*", "never said sorry", "for *leaving.*"],
17: ["The balloons", "were *never*", "the sorrys", "*you owe.*", "They're the sorrys", "people owe *you.*"],
18: ["Maya turned", "to the class.", "\"We did this.", "Every name", "we called him.", "Every paper", "we threw.\""],
19: ["Silence.", "Then Jake whispered,", "\"*Sorry,* Ezra.\"", "*Pop.*"],
20: ["\"*Sorry.*\"", "*Pop.*", "\"I'm sorry, Ezra.\"", "*Pop.*", "*Pop.*", "*Pop.*"],
21: ["*Forty-two*", "sorrys later,", "Ezra floated down,", "right into", "their *arms.*"],
22: ["Now Ezra", "walks to school.", "And Maya's", "*gray balloon?*", "She still has it.", "But she doesn't", "hold it", "*alone* anymore."],
23: ["Like and *subscribe...*", "or that's", "one more balloon", "for *me.*"],
}
caps = []
lines = T['lines']
for li, L in enumerate(lines):
    a, b = L['start'], L['end']
    speech = [i for i in range(a, b) if True]
    # speech frames inside the line, skipping internal pauses (>=7 silent frames)
    sil = [mask[i] == 0 for i in range(a, b)]
    keep = []; i = 0
    while i < len(sil):
        if sil[i]:
            j = i
            while j < len(sil) and sil[j]: j += 1
            if j - i < 7: keep += list(range(a + i, a + j))
            i = j
        else:
            keep.append(a + i); i += 1
    keep = keep or list(range(a, b))
    chunks = CH[L['n']]
    lens = [len(c.replace('*', '')) + 2 for c in chunks]; tot = sum(lens); acc = 0
    starts = []
    for c, l in zip(chunks, lens):
        starts.append(keep[min(len(keep) - 1, int(acc / tot * len(keep)))]); acc += l
    nxt = lines[li + 1]['start'] if li + 1 < len(lines) else N + 14
    for k, c in enumerate(chunks):
        s0 = starts[k]; e0 = (starts[k + 1] - 1) if k + 1 < len(chunks) else min(nxt - 1, b + 12)
        caps.append([s0 + 1, e0 + 1, c])
POPS = [2506, 2554, 2611, 2632, 2653] + [2615 + k * 5 for k in range(11)] + [2680 + k * 4 for k in range(26)]
S = 'sfx/'
sfx = [[187, S + 'pop.wav', 0.8], [259, S + 'whoosh.wav', 0.35], [398, S + 'whoosh.wav', 0.35], [564, S + 'boing.wav', 0.5],
       [813, S + 'sad_wah.wav', 0.4], [913, S + 'whoosh.wav', 0.4], [1041, S + 'laugh_hits.wav', 0.45], [1281, S + 'whoosh.wav', 0.5],
       [1422, S + 'sting.wav', 0.6], [2037, S + 'boom.wav', 0.9], [2771, S + 'ding.wav', 0.35], [3017, S + 'whoosh.wav', 0.35]]
for i, p in enumerate(POPS):
    sfx.append([p + 1, S + 'pop.wav', 0.75 if i < 5 else 0.35])
json.dump({'captions': caps, 'sfx': sfx}, open('cues_film.json', 'w'), indent=0)
print(len(caps), 'captions;', len(sfx), 'sfx'); print(caps[:6]); print(caps[-4:])
