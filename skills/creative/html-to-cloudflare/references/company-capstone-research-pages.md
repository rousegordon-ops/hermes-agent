# Company / capstone research pages

Use this for generated research briefs that help Gordon or family compare nearby companies and frame student capstone/project outreach.

## Page pattern proven in SLO robotics/drone session

- Place as a public wiki-style HTML page under `/opt/data/hermes-pages/wiki/projects/<slug>.html` when it is an engineering/research note.
- Add an extensionless link to `/opt/data/hermes-pages/wiki/index.html` under **Engineering Notes** when the topic is technical rather than personal/project management.
- Keep the page public by default: do not add a `wiki_auth` guard unless Gordon asks.
- Use high-contrast dark styling consistent with existing engineering-note pages.
- Prefer card/section layout over dense tables; Telegram/page consumers often read on mobile.

## Research content shape

For each company:
- Company name with outbound source link.
- Location/proximity signal, especially when “near” is part of the prompt.
- Product/technology direction from public sources only.
- Tags for quick scanning.
- 3–5 student-scale capstone ideas aligned to the public roadmap.

For capstone ideas:
- Frame as subsystem prototypes, test fixtures, diagnostic tools, data pipelines, or simulation-only studies rather than “build a whole product.”
- For defense/counter-UAS topics, avoid weaponized build instructions. Keep projects in detection, simulation, telemetry, safety, operator-awareness, passive RF sensing, or hardware-in-the-loop testing unless there is explicit supervised academic scope.
- Emphasize EE-friendly work: power, RF, sensing, embedded interfaces, telemetry, motor/actuator diagnostics, timing/synchronization, field reliability.

## Verification checklist

1. Grep the on-disk HTML for every intended company and for repeated `Capstone ideas` sections before committing/deploying.
2. Verify the canonical extensionless URL contains at least one late-page sentinel company name.
3. Verify the wiki index contains the new slug.
4. If the canonical URL briefly serves the homepage fallback after deploy, verify the preview URL and the `.html?cb=<commit>` URL, then retry canonical with no-cache headers.

## Session notes: SLO robotics/drone page

The session created `/wiki/projects/slo-robotics-drone-capstone-companies` covering:
- Inspired Flight Technologies
- Zone 5 Technologies
- Trust Automation
- Edge Autonomy / Redwire
- TRIC Robotics
- FarmBot
- Scout AI

Useful source-finding queries included:
- `San Luis Obispo robotics drone companies autonomy UAS Cal Poly SLO`
- `San Luis Obispo CA autonomous systems robotics company drones unmanned aerial systems`
- company-specific searches for Edge Autonomy VXE30/Stalker, Trust Automation SUADS/GAT, TRIC Robotics UV-C strawberries, FarmBot SLO, Scout AI Paso Robles.
