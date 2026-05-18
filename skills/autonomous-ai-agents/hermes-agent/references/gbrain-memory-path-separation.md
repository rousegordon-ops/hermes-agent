# Gordon: Hermes native memory vs gbrain paths

Context from 2026-05-18 conversation with Gordon.

## Current Railway/Hermes environment

- `HERMES_HOME=/opt/data`.
- Hermes native memory therefore lives at `/opt/data/memories/` and should stay there.
  - `/opt/data/memories/MEMORY.md`
  - `/opt/data/memories/USER.md`
- `/opt/data/memories/` also currently contains broader markdown knowledge-store directories (`entities/`, `concepts/`, `projects/`, `queries/`, etc.), which caused confusion because it looks like Gordon's durable gbrain-style store is named “memories”.
- `/opt/data/gbrain/` currently exists but is the upstream/source checkout of `garrytan/gbrain`, not Gordon's durable data store.

## Gordon preference

Gordon considers renaming the gbrain stats/store concept from `gbrain` to `memories` a mistake because it causes recurrent confusion. Prefer `gbrain` terminology for the durable knowledge/stats store. Keep “Hermes memory” reserved for the native hot-cache injected into sessions.

## Original gbrain implementation layout

Original gbrain separates three concerns:

1. **gbrain implementation repo**
   - Example docs use `~/gbrain` as the source checkout.

2. **gbrain runtime/config/local DB**
   - Default config dir: `~/.gbrain`.
   - Default PGLite database path: `~/.gbrain/brain.pglite`.
   - `GBRAIN_HOME` is a parent override; gbrain appends `.gbrain` itself.
     - If `GBRAIN_HOME=/opt/data`, config dir becomes `/opt/data/.gbrain`, DB `/opt/data/.gbrain/brain.pglite`.

3. **content sources inside a brain**
   - Registered with `gbrain sources add <id> --path <path>`.
   - A source is a named repo/folder inside one brain database; route with `--source`, `GBRAIN_SOURCE`, `.gbrain-source`, or `sources.local_path`.
   - A brain is the DB axis; a source is the repo/content axis.

## Recommended local naming split

When cleaning up Gordon's environment, avoid overloading `/opt/data/memories` or `/opt/data/gbrain`:

- Hermes native memory: `/opt/data/memories`.
- gbrain source checkout: `/opt/data/repos/gbrain` or `/opt/data/gbrain-src`.
- gbrain runtime/config/DB: `/opt/data/.gbrain/brain.pglite` if using original gbrain conventions with `GBRAIN_HOME=/opt/data`.
- Gordon's durable markdown source path: `/opt/data/gbrain` is acceptable if Gordon wants the human-facing name, but in original gbrain terms this is a **source path**, not the DB itself.

## Pitfall

Do not blindly rename `/opt/data/memories` to `/opt/data/gbrain`: Hermes native memory depends on `$HERMES_HOME/memories`. If a migration is done, first separate Hermes native memory from the durable gbrain-style source and keep compatibility until all references are updated.