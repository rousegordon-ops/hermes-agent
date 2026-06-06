# Home renovation wiki pages on hermes-pages

Use this reference when Gordon asks to add or update house-renovation research in the personal wiki (solar, fixtures, electrical rough-in, bathroom products, etc.).

## Placement and URL conventions

- Source repo: `/opt/data/hermes-pages`.
- Wiki hub index: `/opt/data/hermes-pages/wiki/index.html`.
- Renovation research pages often live as HTML files under `wiki/projects/` even when the hub link appears under the **Home Renovation** section.
- Link from the Home Renovation section using extensionless hrefs, e.g. `/wiki/projects/solar-options`.
- Product utility list pages can live at root-level public paths, e.g. `/showerheads`, `/bathroom-vanity-lights`, `/recessed-gimbal-lights`.

## Auth/public handling

- Do not assume every `/wiki/projects/...` page should be public. Match nearby pages unless Gordon explicitly asks for public access.
- If a page should be public, remove the client-side `wiki_auth` login redirect script and verify both locally and live that `wiki_auth`/`/wiki/login` are absent.
- Root-level utility/product pages should remain public unless Gordon explicitly requests a proper root-scoped auth flow.

## Home-renovation page workflow

1. Read the current target page and `wiki/index.html` before editing.
2. Create or patch hand-written HTML directly under `/opt/data/hermes-pages/wiki/...`.
3. Add a simple `<li><a href="...">Title</a></li>` in the appropriate `wiki/index.html` section. No summaries/descriptions in the hub list.
4. If the page needs illustrations, prefer local self-contained SVGs under `/opt/data/hermes-pages/wiki/assets/` unless a licensed/downloaded image is necessary.
5. Commit only relevant files from `/opt/data/hermes-pages`, push with `GIT_TERMINAL_PROMPT=0`, then deploy via Wrangler Direct Upload:
   ```bash
   npx -y -p node@22 -p wrangler wrangler pages deploy /opt/data/hermes-pages --project-name hermes-pages --commit-dirty=true
   ```
6. Verify canonical URLs on `https://hermes-pages-d55.pages.dev`, not only the Wrangler preview URL.

## Verification pattern

Use Python `urllib.request` with expected text needles for every changed page and asset, e.g.:

```python
import urllib.request
base='https://hermes-pages-d55.pages.dev'
checks={
  '/wiki/projects/solar-options-planning':['Planning for Solar Later','solar-ready-rough-in.svg'],
  '/wiki/projects/solar-options':['Planning while walls are open','/wiki/projects/solar-options-planning'],
}
for path, needles in checks.items():
    html=urllib.request.urlopen(urllib.request.Request(base+path,headers={'User-Agent':'Mozilla/5.0'}),timeout=30).read().decode('utf-8','replace')
    assert all(n in html for n in needles), path
```

## Solar / planning-during-construction notes

For Ventura solar planning pages, Gordon's situation includes a large south-facing roof and open walls during electrical rough-in. The solar planning material should live on a dedicated construction-phase subpage (currently `/wiki/projects/solar-options-planning-during-construction`) rather than being spread across every solar subpage; overview/conventional/decision pages should carry short callouts that link to it. If renaming/moving a wiki page, add a `_redirects` entry from the old extensionless URL and verify the redirect.

Gordon's current preference for this class of work: assume eventual **whole-home backup with smart load management**, but do only construction-phase work that would be significantly more expensive, ugly, or disruptive after drywall. Do not push premature vendor-specific battery/inverter/smart-panel decisions.

Key guidance to preserve in future edits:

- Oversized empty conduit from attic/roof area to electrical equipment area.
- Preserve main-panel/service capacity and spare breaker spaces for solar, battery, EV, and electrification.
- Reserve wall space near main service equipment for future gateway/transfer equipment, meters, disconnects, and load-management hardware.
- If there is no good battery location near the main panel, identify plausible remote battery locations and preserve hidden conduit/pathways from the main electrical/gateway area to those locations; add pull strings and labels, but do not assume final AC vs DC/proprietary conductor architecture.
- Add backing/blocking, working clearance, and serviceable space at likely remote battery/equipment walls where low-cost during construction.
- For likely whole-home backup with smart load management, emphasize gateway/load-management space, large-load circuit labeling, and control pathways; avoid over-investing in a small critical-loads subpanel unless the electrician/installer says it is uniquely cheap or required now.
- Keep HVAC, heat-pump water heater, dryer, oven/range, EV charger, pool/spa, and other large-load circuits identifiable and accessible for future smart load modules/contactors/smart-panel work.
- Add Ethernet/low-voltage/control conduit to the solar/gateway/battery equipment areas.
- Photograph and label open-wall routing, panel bays, blocking, and conduits before insulation/drywall.
- Keep plumbing/gas/storage obstructions away from likely equipment walls and keep roof penetrations away from the prime south-facing solar plane.
- Coordinate with electrician and, if possible, a future solar installer before drywall; final BESS location/design still needs code, fire, manufacturer, and permitting review.

## Known deployment quirk

Wrangler may warn that `/opt/data/hermes-pages/wrangler.jsonc` is missing `pages_build_output_dir` and is ignored. This warning is non-blocking for direct `wrangler pages deploy /opt/data/hermes-pages --project-name hermes-pages --commit-dirty=true` deployments; still verify live content afterward.
