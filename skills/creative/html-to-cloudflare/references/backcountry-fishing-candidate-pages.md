# Backcountry fishing candidate pages

Use this when Gordon asks to add or expand a Sierra backcountry fishing candidate under `/wiki/hobbies/`.

## User fit criteria

Gordon's benchmark is Sheep Crossing on the North Fork San Joaquin: steep granite canyon, defined plunge pools, wild trout, solitude, and a campable 2–3 night backpack. New candidates should be judged against that whole experience, not just fish density.

Stable preferences from recent fishing sessions:
- Close-to-Dublin candidates matter; call out drive time from Dublin, CA when comparing options.
- A candidate can be valuable as a **timberline/high-country variant**, but say clearly if the timberline terrain and the best creek fishing are not co-located.
- Distinguish lake/basecamp trips from true creek/pocket-water trips. Do not oversell lake/reservoir scenery as matching the plunge-pool benchmark.
- For practical pages, include a clear verdict: best first bet, best logistics, benchmark fit, and risks.

## Recommended page structure

For a new candidate page such as `sonora-pass-pct-leavitt-peak.html` or `clark-fork-kennedy-meadows.html`:
1. Hand-edit public HTML under `/opt/data/hermes-pages/wiki/hobbies/<slug>.html`.
2. Use high-contrast dark styling consistent with existing hobbies pages.
3. Include:
   - Short verdict / why this candidate exists.
   - Drive time from Dublin, ideally no-traffic OSRM estimate with caveat.
   - Trailhead / permit / season logistics.
   - "Fit against North Fork San Joaquin benchmark" section.
   - 2–3 night itinerary concept, labeled as a planning sketch rather than navigation instructions.
   - Pictures stored locally under `/wiki/assets/<slug>/` with concise credits.
   - Source links to Forest Service / CDFW / county fishing pages / PCTA where applicable.
4. Add an extensionless link in `/opt/data/hermes-pages/wiki/index.html` under Hobbies.
5. Add or update a link from `/wiki/hobbies/backcountry-fishing.html` so the candidate is discoverable from the main fishing page.
6. Commit, push, deploy with Wrangler Direct Upload, and verify the canonical URL and asset URLs.

## Drive-time workflow from Dublin

Use the maps skill / OSRM for factual drive times; do not estimate mentally.

Useful origin:
- Dublin, CA coordinates used in-session: `37.7021521,-121.9357918`.

For named places, try the maps skill first:
```bash
python3 /opt/hermes/skills/productivity/maps/scripts/maps_client.py distance 'Dublin, California' --to 'Sonora Pass, California' --mode driving
```

If geocoding fails, geocode/search separately or use known coordinates with OSRM:
```python
import urllib.request, json
origin=(37.7021521,-121.9357918)
dest=(38.3279273,-119.6371813)  # Sonora Pass
url=f"https://router.project-osrm.org/route/v1/driving/{origin[1]},{origin[0]};{dest[1]},{dest[0]}?overview=false"
data=json.load(urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'HermesAgent/1.0'}),timeout=30))
minutes=data['routes'][0]['duration']/60
miles=data['routes'][0]['distance']/1609.344
```

Always label these as **no-traffic estimates**.

## Recently evaluated candidate signals

- **Clark Fork / Iceberg Meadow**: strongest sub-4-hour creek-shape candidate from Dublin; likely below timberline. Good for possible pocket/cascade water, not a clean timberline trip.
- **Kennedy Meadows / Relief Reservoir / Emigrant**: strongest logistics candidate under 4 hours; more lake/granite/basecamp oriented unless specific moving-water targets are confirmed.
- **Sonora Pass / PCT / Leavitt Peak**: shortest-drive true timberline feel. Best creek fishing is adjacent/lower at Leavitt Meadows / West Walker, not on the exposed PCT crest.
- **Golden Trout Wilderness / Cottonwood Creek**: iconic golden trout / high-country trip, but far from Dublin and not a short-drive candidate.

## Verification checklist

Before publishing:
- Assert the candidate page contains expected `<h1>`, itinerary heading, and local asset paths.
- Assert public pages do not contain `wiki_auth` or `/wiki/login?dst=` unless privacy was explicitly requested.
- Assert `/wiki/index.html` contains the candidate link.
- Assert `/wiki/hobbies/backcountry-fishing.html` links to the candidate where relevant.
- Assert each local asset exists and has nonzero size.
- After Wrangler deploy, verify canonical page content, index link, backcountry-fishing link, and asset URLs. If `/wiki/` is stale right after deploy, retry; Cloudflare can lag the preview/canonical edge for a few seconds.