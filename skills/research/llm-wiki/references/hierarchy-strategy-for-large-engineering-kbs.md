# Hierarchy Strategy for Large Engineering Knowledge Bases

Captured from a discussion comparing Gordon's agent-inferred static LLM wiki hierarchy with the more programmatic approach in `nashsu/llm_wiki`.

## Current Gordon/public static KB behavior

- Hierarchy is primarily LLM/agent-inferred from semantic structure and user intent.
- It is agent-maintained over time; "human maintained" means human-curated/overseen, not that the user manually edits hierarchy.
- The agent should automatically re-evaluate topology during substantial updates: update existing pages, create child pages, split oversized pages, add intermediate hubs, move shared material upward, add cross-links, update sources, and preserve old URLs when pages move.
- Existing rules are qualitative prompt rules, not deterministic constraints: semantic containment, concise hub pages, split large/duplicative sections, child/back links, top index contains only major hubs.
- There is no hard encoded max-child rule today. A sensible future policy is soft max 7±2 children per parent; review threshold at 10+ children; root nav ~6-10 major hubs.

## What nashsu/llm_wiki adds programmatically

Observed from the repo README/code:
- Two-step ingest: analysis first, then generation.
- Persistent ingest queue with crash recovery/retry/cancel.
- Knowledge graph from `[[wikilinks]]`.
- 4-signal graph relevance: direct links, source overlap, Adamic-Adar/common neighbors, type affinity.
- Louvain community detection with cohesion and top nodes.
- Optional vector semantic search.
- Review workflow for contradictions, duplicates, missing pages, and suggestions.

## Trade-off

Agent-inferred hierarchy is strong for small/medium curated expert KBs where a human-readable teaching structure matters more than deterministic clustering. It can produce better narrative topology, e.g. fundamentals → mechanisms → reliability → applications → latest research.

Programmatic graph/hierarchy support scales better for large, continuously updated, multi-user engineering KBs because it can recompute structure signals, detect orphans/duplicates/stale pages, and expose cluster metrics. However, graph clusters are not automatically good navigation; they need LLM naming/synthesis and sometimes human approval.

## Recommended scalable architecture

Use a hybrid:
1. Programmatic substrate enforces invariants and computes signals:
   - stable page IDs/slugs
   - backlinks and broken-link checks
   - source provenance
   - freshness/staleness
   - duplicate/orphan detection
   - graph communities and cohesion
   - max page size and max child count warnings
   - redirect preservation
   - review queues
2. LLM semantic maintainer uses those signals to:
   - name clusters
   - write hub summaries
   - decide when a cluster deserves a hub
   - split/merge pages
   - convert raw docs into readable wiki pages
   - explain contradictions
   - propose topology refactors
3. Human approval gates for disruptive topology changes:
   - automatic: small updates, new cross-links, ordinary child pages, minor page splits
   - review required: moving/renaming major hubs, merging/deleting pages, re-homing many pages

## Practical guidance for future answers

When asked which approach scales for an internal engineering team, recommend the hybrid. Say: program computes structure signals and enforces invariants; LLM turns them into human-usable hierarchy; humans approve disruptive refactors.
