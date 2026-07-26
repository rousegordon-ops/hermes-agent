# Backcountry fishing candidate research notes

Use when enriching Gordon's `/wiki/hobbies/backcountry-fishing` page or evaluating additional Sierra backcountry trout destinations.

## Gordon's fit criteria

- Primary benchmark: Sheep Crossing on the North Fork San Joaquin — steep granite canyon, large plunge pools, wild trout, solitude.
- Preferred water: steep remote creeks, pocket water, boulder-choked canyons, defined plunge pools; avoid flat meadow meanders as primary recommendations.
- Off-road exclusion: Gordon does not want to hike into a lake/camp/fishing corridor and find Jeeps or side-by-sides there. Exclude or hard-deprioritize destinations where OHV/high-clearance 4WD roads reach the lake basin, camp zone, or adjacent fishing corridor.
- Trip profile: 2–3 nights, good camping near water, some tree cover, real solitude, ideally a view.
- Hike-in: 3–6 miles preferred when possible; longer trips can be included if clearly marked as longer-haul variants.
- High-country/timberline variant: acceptable when the trip climbs to timberline/alpine benches, but still flag whether the fishing is lake-first vs moving-water/pocket-water.

## Candidate framing pattern

For each candidate, write a terse note with:

1. Area / wilderness.
2. Why it might fit.
3. Caveat vs NFSJ benchmark.
4. Research angle: what to verify before treating it as a strong candidate.
5. Official/logistics link where possible.

Avoid overstating lake-heavy alpine basins as direct replacements for Sheep Crossing. Label them as `timberline variant`, `lake-first`, `longer-haul`, or `needs moving-water verification`.

## Short-drive timberline / granite findings from 2026-07 session

When Gordon asks for *shortest drive from Dublin to timberline with decent creek fishing*, first check the geography split:

- **Yosemite / Vogelsang / Fletcher Creek / Lewis Creek** — best under-5-hour granite/timberline candidate with no off-road surprise. Tuolumne Meadows routed ~4.5 hours from Dublin in no-traffic OSRM. Classic Yosemite granite around ~9,500–10,500 ft; fishing is integrated via Fletcher/Lewis/Rafferty and optional Lyell/Dana Fork time, but it is not an NFSJ-style plunge-pool canyon. Detail page: `/wiki/hobbies/yosemite-vogelsang-fletcher-creek`.
- **Kennedy Meadows → Summit Creek / Granite Dome** — best shorter-drive granite/stream option. Kennedy Meadows routed ~3h34m from Dublin; Relief Reservoir is below timberline, but pushing toward Summit Creek/Granite Dome gives stronger granite/high-country fit and keeps vehicles out once inside Emigrant Wilderness. Detail page: `/wiki/hobbies/kennedy-meadows-granite-dome`.
- **Clark Fork / Kennedy Meadows** — best practical sub-4-hour logistics/fishing access, but mostly below timberline. Clark Fork/Iceberg Meadow is a forested creek/meadow trip; Kennedy/Relief Reservoir is lower and not true timberline. Detail page: `/wiki/hobbies/clark-fork-kennedy-meadows`.
- **Carson Pass / Round Top / Winnemucca / Fourth of July Lake / Summit City Creek** — formerly the best short-drive granite/timberline-ish candidate, but removed from the shortlist because the Forestdale Divide / Blue Lakes side has 4WD access near Summit City Trail/Creek. Do not recreate unless Gordon explicitly relaxes the no-OHV criterion.
- **Sonora Pass / PCT / Leavitt Peak** — fastest/cleanest timberline access, but more volcanic and removed from the shortlist because Leavitt Lake is accessible by rough high-clearance 4WD road. Do not recreate unless Gordon explicitly relaxes the no-OHV criterion.
- **Ebbetts/Highland Lakes/Noble/Silver Creek** — possible short-drive high-country granite-ish option, but hard-deprioritize: Highland Lakes/Blue Lakes/Forestdale area has dirt/OHV/4WD access and Gordon had poor Mokelumne/Hwy 4 headwaters fishing.

For these mixed-fit trips, explicitly distinguish: `short-drive logistics`, `granite vs volcanic feel`, `timberline scenery`, `fishable moving water`, and `off-road vehicle exposure`. Do not collapse them into one score.

## Timberline candidates added in 2026-07 session

- **Golden Trout Lakes from Onion Valley — John Muir Wilderness**
  - Official link: `https://www.fs.usda.gov/r05/inyo/recreation/trails/golden-trout-lakes-trail`
  - Forest Service describes the route as primitive, steep, rugged, difficult to follow; about 2,200 ft gain in 2.2 mi to lakes between Dragon Peak and Kearsarge Peak.
  - Framing: strong short timberline/alpine candidate, but lake-first. Verify camps and whether inlets/outlets offer meaningful moving-water fishing.

- **Fish Creek / Iva Bell / Tully Hole corridor — Ansel Adams Wilderness**
  - Official link: `https://www.fs.usda.gov/r05/inyo/recreation/trails/fish-creek-trail`
  - Forest Service notes the trail follows Crater Creek into Fish Creek Valley, reaches Iva Bell around 11 mi, and continues toward Cascade Valley / Tully Hole and JMT/PCT connections.
  - Framing: longer 2–3 night candidate with named creek corridor and high-country continuation. Verify overgrowth/trail condition and whether fishing/camping justify the longer approach.

- **Piute Pass / Humphreys Basin / upper Piute Creek — John Muir Wilderness**
  - Official link: `https://www.fs.usda.gov/r05/inyo/recreation/trails/piute-pass-trail-north-lake`
  - Forest Service notes the route starts in lodgepole/aspen, climbs granite benches past lakes to Piute Pass, then descends Piute Creek toward Hutchinson Meadow.
  - Framing: excellent timberline/high-alpine camping and scenery; more basin/lake-oriented than plunge-pool canyon. Treat as a variant, not a direct Sheep Crossing replacement.

- **North Fork Big Pine Creek / Big Pine Lakes — John Muir Wilderness**
  - Official link: `https://www.fs.usda.gov/r05/inyo/recreation/trails/big-pine-creek-north-fork-trail`
  - Forest Service highlights First Falls, North Fork canyon, Big Pine Lakes, Temple Crag, Palisade Glacier views, cirques and glaciated granite.
  - Framing: high scenic/timberline candidate but likely crowded and lake-focused. Keep only if creek sections between lakes have worthwhile pocket water.

## Deployment note

For `/opt/data/hermes-pages/wiki/hobbies/backcountry-fishing.html`, direct GitHub push is not enough. After commit/push, run the normal Wrangler Pages deploy and verify raw canonical HTML contains new candidate names. Text extraction summaries can truncate or summarize away the exact added strings; raw HTML verification is more reliable.