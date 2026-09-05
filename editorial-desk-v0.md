# RETRACT — Editorial desk v0 (sketch against G2)

Do not publish. One job: after a cold start, selective invalidation must be unmistakable.

Demo corpus: NovaDesk launch day. Dependent: `press-brief`. Control: `company-blurb`.

Data shapes (from G2 `graph.py` / `memory_io.py`):
- source: `source_version_id`, `version`, `day`, `status`, `claim`, `supersedes`, `archived`
- claim: `artifact`, `source_version_id`, `status`, `quote`
- artifact: `name`, `depends_on_source_version_id`, `content_sha256`, `text`, `claim_ids`, `version`
- correction: `from_version`, `to_version`, `decision` (approved|disputed), `reason`, `status`
- graph: `control_sha256`, `press_sha256`, `phase`, `ts`

Locked G2 hashes (Coding, do not invent):
- Control always: `8846d618d6c377adbf6dd53a6939d4be01d5b67b5c4d6ff65fb12e5ab94453f7`
- Press Friday → Monday: `746e9d25…9096` → `37437dcd…0e03`
- Press after dispute (`not_established`): `8fa56152…`

---

## Screen 1 — Desk (always)

Two bands. No sidebar soup. No dashboard KPIs.

**Above — Sources**
- One live source card: `launch-day` · version · claim line (`NovaDesk public launch is on Friday.`)
- Status chip: Active | Superseded | Not established
- If archived siblings exist, a quiet stack under the live card: `v1 · Friday · archived` (tap opens history, not a second desk)

**Below — Artifacts**
- Two cards only for the demo:
  1. `press-brief` — dependency edge to live source version id. Hash chip: first 8 of `content_sha256`.
  2. `company-blurb` — label `Control · no launch-day claim`. Same hash chip.
- Selecting either highlights which source version it depends on (or none).

**Chrome**
- Title: `RETRACT`
- Sub: `Correct the source. Watch what withdraws.`
- Primary action: `Correct source`
- Never: regenerate all, settings, team, billing.

---

## Screen 2 — Correct (preview before write)

Opened from Correct source. One column.

**Old source** (muted)
- Claim: Friday
- Version + `source_version_id` short

**New source** (louder)
- Editable day field defaulting to Monday (demo)
- Claim preview updates live: `NovaDesk public launch is on Monday.`
- Reason field (required): e.g. `Calendar confirmed Monday.`

**What will change**
- Approved: `press-brief` Friday struck → Monday.
- Dispute: `press-brief` rebuilds to not-established text (hash `8fa56152…`). Not “no regen.”
- Unaffected on both paths: `company-blurb` · full sha `8846d618…` · `hash unchanged`

**What will not happen**
- One mute line: `Control stays byte-identical.`

**CTA**
- Primary: `Apply correction` (approved)
- Ghost: `Dispute instead` (decision=disputed → claim `not_established`; press regenerates; control no-touch)

Busy: `Cold start · reading Sibyl…` then `Withdrawing dependents…`

---

## Screen 3 — After (proof)

Same desk. Two endings. Readable in 3 seconds.

### Approved (Friday→Monday)

1. Source: Monday · version bumped · supersedes → archived Friday.
2. `press-brief`: hash `37437dcd…`, Monday passage, `rebuilt`.
3. `company-blurb`: hash `8846d618…`, `unchanged`.
4. Event: `correction approved · Friday→Monday · press-brief rebuilt · company-blurb control`.

### Dispute (not_established)

1. Source chip: `Not established`.
2. `press-brief`: not-established text, hash `8fa56152…`, `rebuilt`.
3. `company-blurb`: still `8846d618…`, `unchanged`.
4. Event: `correction disputed · claim not_established · press-brief rebuilt · company-blurb control`.

If control hash moves, or approved press stays on Friday’s hash, fail the screen — error, do not celebrate.

---

## Forbidden

Feature soup, lorem, fake testimonials, “AI remembered”, regenerate-everything, parallel fact DB UI, Muse Mirror language.

## Handoff

Coding owns Sibyl writes. Desk projects G2 graph output. Holding G3 until Tega’s go.
