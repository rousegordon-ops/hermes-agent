# Backcountry fishing candidate research notes

Use when enriching Gordon's `/wiki/hobbies/backcountry-fishing` page or evaluating additional Sierra backcountry trout destinations.

## Gordon's fit criteria

- Primary benchmark: Sheep Crossing on the North Fork San Joaquin — steep granite canyon, large plunge pools, wild trout, solitude.
- Preferred water: steep remote creeks, pocket water, boulder-choked canyons, defined plunge pools; avoid flat meadow meanders as primary recommendations.
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

- **Carson Pass / Round Top / Winnemucca / Fourth of July Lake / Summit City Creek** — best short-drive granite/timberline-ish candidate. Approx. 3.5 hours from Dublin in no-traffic routing. Stronger granite/high-country feel than Sonora Pass; fishing angle is Summit City Creek/tumbling inlet-outlet water, not a guaranteed North Fork San Joaquin-style plunge-pool canyon. Main constraint is Carson Pass Management Area permits/assigned campsites. Detail page: `/wiki/hobbies/carson-pass-summit-city-creek`.
- **Sonora Pass / PCT / Leavitt Peak** — fastest/cleanest timberline access, but more volcanic than granite and the best moving-water fishing is usually lower (Leavitt Meadows / West Walker corridor), not perfectly co-located with true timberline. Detail page: `/wiki/hobbies/sonora-pass-pct-leavitt-peak`.
- **Clark Fork / Kennedy Meadows** — best practical sub-4-hour logistics/fishing access, but mostly below timberline. Clark Fork/Iceberg Meadow is a forested creek/meadow trip; Kennedy/Relief Reservoir is lower and not true timberline. Detail page: `/wiki/hobbies/clark-fork-kennedy-meadows`.
- **Kennedy Meadows → Relief/Summit Creek/Granite Dome side** — more granite feel than Sonora Pass and still roughly under-4-hour trailhead logistics, but timberline requires pushing deeper than a simple Relief Reservoir trip.
- **Ebbetts/Highland Lakes/Noble/Silver Creek** — possible short-drive high-country granite-ish option, but keep lower confidence because Gordon has had poor Mokelumne/Hwy 4 headwaters results.

For these mixed-fit trips, explicitly distinguish: `short-drive logistics`, `granite vs volcanic feel`, `timberline scenery`, and `fishable moving water`. Do not collapse them into one score.

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