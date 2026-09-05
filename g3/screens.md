# G3 screens — layout + copy for Coding

Viewport: desktop 1280, also readable at 390. One column desk, max width 720, centered. Dark paper `#0E0F10`, ink `#F2EFE8`, mute `#9A958C`, accent metal `#C4B59A`. No sidebar. No dashboard KPIs. No lorem.

Hash chips always show first 8 + ellipsis; on the control card also expose full sha on hover/title.

---

## Screen A — Desk (before)

**Chrome**
- Wordmark: `RETRACT`
- Sub: `Correct the source. Watch what withdraws.`
- Trailing text button: `Correct source`

**Band 1 — Sources** (label: `Source`)
- Card `novadesk-launch`
  - Eyebrow: `v1 · active`
  - Claim: `NovaDesk public launch is on Friday.`
  - Meta: `source 5858bd57…`
  - No archived stack yet

**Band 2 — Artifacts** (label: `Generated`)
1. Card `press-brief`
   - Status: `depends on launch`
   - Body (mono, 3 lines):
     ```
     Embargo lifts: Friday
     Headline: NovaDesk launches to the public on Friday.
     Call to action: Mark your calendar for Friday.
     ```
   - Hash chip: `746e9d25…`
2. Card `company-blurb`
   - Status: `Control · no launch-day claim`
   - Body:
     ```
     NovaDesk is a fictional productivity suite owned by the RETRACT demo corpus.
     Mission: calm desks, clear calendars.
     ```
   - Hash chip: `8846d618…` (title = full sha)

Selecting an artifact draws a 1px metal edge on the source it depends on (press → launch; blurb → none).

---

## Screen B — Correct (preview)

Full-screen sheet over the desk. Back chevron closes.

**Title:** `Correct source`  
**Intro:** `Old claim stays readable. Dependents that cite it will withdraw.`

**Old** (muted card)
- Label: `Current`
- Claim: `NovaDesk public launch is on Friday.`
- Meta: `v1 · 5858bd57…`

**New** (louder card)
- Label: `Proposed`
- Field `Day` default `Monday`
- Live claim: `NovaDesk public launch is on Monday.`
- Field `Reason` (required): placeholder `Calendar confirmed Monday.`

**What will change**
- Row `press-brief` — passage diff:
  - struck: `Friday`
  - insert: `Monday`
  - lines: Embargo / Headline / CTA
- Note: `Hash will move off 746e9d25…`

**What will not change**
- Row `company-blurb` — `hash unchanged` · `8846d618d6c377adbf6dd53a6939d4be01d5b67b5c4d6ff65fb12e5ab94453f7`
- Mute line: `Control stays byte-identical.`

**CTAs**
- Primary: `Apply correction` → approved ending (Screen C1)
- Ghost: `Dispute instead` → dispute ending (Screen C2)
- Ghost disabled until reason length ≥ 8

**Busy (after click)**
1. `Cold start · reading Sibyl…`
2. `Withdrawing dependents…`

Do not draw a second “regenerate all” button.

---

## Screen C1 — After · approved

Same desk chrome. Event strip under sub:
`correction approved · Friday→Monday · press-brief rebuilt · company-blurb control`

**Source**
- Eyebrow: `v2 · active · supersedes 5858bd57…`
- Claim: `NovaDesk public launch is on Monday.`
- Quiet archive row: `v1 · Friday · archived · supersede Friday→Monday`

**press-brief**
- Status: `rebuilt`
- Body Monday lines (exact G2):
  ```
  Embargo lifts: Monday
  Headline: NovaDesk launches to the public on Monday.
  Call to action: Mark your calendar for Monday.
  ```
- Hash: `37437dcd…` (must differ from before)

**company-blurb**
- Status: `unchanged`
- Hash: `8846d618…` identical to before (full match)
- Body unchanged

**Fail state (do not celebrate):** if control hash ≠ `8846d618…` or press hash still `746e9d25…`, show banner `Proof failed · selective invalidation broken.`

---

## Screen C2 — After · dispute

Event strip:
`correction disputed · claim not_established · press-brief rebuilt · company-blurb control`

**Source**
- Eyebrow: `v2 · not established`
- Claim: `NovaDesk public launch day is not established.`
- Archive row: `v1 · Friday · archived · dispute Friday→not_established`

**press-brief** (rebuilds — not “no regen”)
- Status: `rebuilt`
- Body (exact G2):
  ```
  Embargo lifts: not established
  Headline: NovaDesk public launch day is not established.
  Call to action: Do not schedule outreach until day is established.
  ```
- Hash: `8fa56152…`

**company-blurb**
- Status: `unchanged`
- Hash: `8846d618…`

**Fail state:** control moved, or press hash still Friday’s.

---

## Coding map

| UI action | G2 surface |
|---|---|
| Load desk | `build_graph("before")` / list sources + artifacts |
| Apply correction | approved path: archive Friday, write Monday source, regen press, journal; control untouched |
| Dispute instead | disputed path: archive Friday, write not_established source, regen press to not-established text, journal; control untouched |
| Hash chips | `content_sha256` on artifact body |
| Event strip | correction entity + journal event |

Projection only in UI. No parallel JSON fact DB.
