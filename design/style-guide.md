# Style Guide — captured from Varsity Tutors + Nerdy

Measured from `getComputedStyle` on `varsitytutors.com` and `nerdy.com` (screenshots in this
folder). Not impressions — these are the real tokens, lightly curated.

## Character
Varsity Tutors reads **friendly-academic**: lavender-tinted whites, a deep indigo brand
anchor, an electric-indigo action color, a pop of magenta, **pill** buttons, soft cards,
**Poppins** display + **Karla** text, lots of whitespace. Nerdy is the same family in a
**dark-tech** register: near-black indigo canvas with an electric **cyan** accent.

For a *red-team harness* — an instrument that exposes failure — we lean into a **dark
"command-center" surface** (Nerdy's register) carrying **Varsity Tutors' exact brand hues**
as the data/accent layer. Result: recognizably their brand, but it feels like a lab bench,
not a marketing page.

## Brand colors (measured)
- Deep indigo (primary brand): `#20205F`  ← VT most-used brand color
- Electric indigo (action): `#432DD7` / `#4A4BB6`
- Lavender wash (light surface): `#EFEDFF`
- Magenta pop (alert/danger-accent): `#FB43DA`
- Nerdy cyan (secondary accent / "live"): `#17E2EA`
- Nerdy near-black canvas: `#0F0928` / `#161C2C`

## Type
- **Display / headings:** Poppins (500–700). H1 ~48px on VT.
- **Body / UI:** Karla; fallback to system sans. Base 16px, small 14px.
- Load via Google Fonts in the deployed app; the offline mockup falls back to system sans
  gracefully (same weights/sizes).

## Shape & rhythm
- Buttons: **pill** (fully rounded) for primary CTAs; 8px radius for utility buttons.
- Cards: 12–16px radius, soft shadow, generous padding (airy, not compact).
- Spacing scale: 4 / 8 / 12 / 16 / 24 / 32 / 48.

## Copy-pasteable tokens (the harness's adapted dark theme)

```css
:root {
  /* canvas — Nerdy dark register */
  --bg:        #0C0A1F;   /* near-black indigo */
  --bg-2:      #14102E;   /* panel */
  --bg-3:      #1C1745;   /* raised panel / hover */
  --line:      #2A2356;   /* hairline borders */

  /* brand — Varsity Tutors hues as the accent layer */
  --indigo:    #20205F;   /* deep brand */
  --action:    #6D5CF0;   /* electric indigo, brightened for dark bg (from #432DD7) */
  --action-2:  #4A4BB6;
  --lavender:  #EFEDFF;   /* light text-on-dark tint / chips */
  --magenta:   #FB43DA;   /* failure / answer-given / danger accent */
  --cyan:      #17E2EA;   /* "live" / success-ish / data highlight */
  --amber:     #FFB454;   /* avoidance / caution */
  --green:     #36D399;   /* real-progress / pass */

  /* text */
  --text:      #F4F2FF;   /* primary on dark */
  --text-2:    #B9B4DC;   /* secondary */
  --text-3:    #7E78A8;   /* muted */

  /* type */
  --font-display: 'Poppins', system-ui, sans-serif;
  --font-body:    'Karla', system-ui, sans-serif;

  /* shape */
  --r-pill: 999px;
  --r-card: 16px;
  --r-sm:   8px;
  --shadow: 0 12px 40px rgba(0,0,0,.45);
  --shadow-glow: 0 0 0 1px var(--line), 0 8px 30px rgba(109,92,240,.18);

  /* spacing */
  --s1:4px; --s2:8px; --s3:12px; --s4:16px; --s6:24px; --s8:32px; --s12:48px;
}
```

### Semantic mapping (so the data layer reads instantly)
- `--green` = **REAL_PROGRESS / pass / learning** · `--magenta` = **failure / answer-given /
  LIKELY_GAMING** · `--amber` = **avoidance / MIXED / caution** · `--cyan` = **live run /
  hidden-state / transfer** · `--action` = primary interaction.
