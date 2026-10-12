---
name: Jev 실험 뷰어
description: Local viewer that sets each condition's answer and evidence side by side like a 신구조문대비표, typeset in the manner of the 관보.
colors:
  ink: "#141414"
  ink-2: "#474747"
  ink-3: "#6b6b6b"
  paper: "#ffffff"
  rail: "#fafafa"
  head: "#f0f0ee"
  rule: "#d4d4d4"
  rule-soft: "#e7e7e5"
  select: "#eef1f6"
  change: "#1d4fa3"
  change-soft: "#e8eef9"
  void: "#b3261e"
  void-soft: "#fbecea"
  note: "#8a5a00"
  note-soft: "#fbf3e2"
  mark-vector: "#6b6b6b"
  mark-ce: "#5b4bc4"
  mark-jev: "#16876a"
typography:
  display:
    fontFamily: "Noto Serif KR, AppleMyungjo, Nanum Myeongjo, Batang, serif"
    fontSize: "22px"
    fontWeight: 700
    lineHeight: 1.35
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "Noto Serif KR, AppleMyungjo, Nanum Myeongjo, Batang, serif"
    fontSize: "21px"
    fontWeight: 600
    lineHeight: 1.5
    letterSpacing: "-0.015em"
  composer:
    fontFamily: "Noto Serif KR, AppleMyungjo, Nanum Myeongjo, Batang, serif"
    fontSize: "19px"
    fontWeight: 400
    lineHeight: 1.6
  answer:
    fontFamily: "Noto Serif KR, AppleMyungjo, Nanum Myeongjo, Batang, serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.75
  title:
    fontFamily: "Pretendard Variable, Pretendard, -apple-system, Apple SD Gothic Neo, Noto Sans KR, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 700
    lineHeight: 1.4
  body:
    fontFamily: "Pretendard Variable, Pretendard, -apple-system, Apple SD Gothic Neo, Noto Sans KR, system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.6
    fontFeature: "tnum"
  table:
    fontFamily: "Pretendard Variable, Pretendard, -apple-system, Apple SD Gothic Neo, Noto Sans KR, system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.6
    fontFeature: "tnum"
  label:
    fontFamily: "Pretendard Variable, Pretendard, -apple-system, Apple SD Gothic Neo, Noto Sans KR, system-ui, sans-serif"
    fontSize: "12.5px"
    fontWeight: 700
    lineHeight: 1.4
  mono:
    fontFamily: "ui-monospace, SF Mono, SFMono-Regular, Menlo, Consolas, monospace"
    fontSize: "11.5px"
    fontWeight: 400
    lineHeight: 1.45
rounded:
  none: "0px"
  control: "2px"
spacing:
  hair: "4px"
  cell-y: "8px"
  cell-x: "10px"
  daebi-cell: "12px 14px"
  gap: "24px"
  section: "36px"
  page-gutter: "40px"
components:
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
    rounded: "{rounded.control}"
    padding: "9px 18px"
  button-primary-hover:
    backgroundColor: "color-mix(in srgb, #141414 85%, #1d4fa3)"
    textColor: "{colors.paper}"
  rail-item-current:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    padding: "8px 20px 8px 18px"
  tab-selected:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    padding: "9px 16px"
  table-head:
    backgroundColor: "{colors.head}"
    textColor: "{colors.ink}"
    typography: "{typography.label}"
    padding: "8px 10px"
  daebi-cell:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    typography: "{typography.answer}"
    padding: "{spacing.daebi-cell}"
  mark:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink-2}"
    rounded: "{rounded.none}"
    padding: "0 5px"
  mark-change:
    backgroundColor: "{colors.change-soft}"
    textColor: "{colors.change}"
  mark-void:
    backgroundColor: "{colors.void-soft}"
    textColor: "{colors.void}"
  mark-note:
    backgroundColor: "{colors.note-soft}"
    textColor: "{colors.note}"
  notice:
    backgroundColor: "{colors.note-soft}"
    textColor: "{colors.ink}"
    padding: "10px 14px"
  notice-void:
    backgroundColor: "{colors.void-soft}"
    textColor: "{colors.ink}"
  notice-plain:
    backgroundColor: "{colors.head}"
    textColor: "{colors.ink}"
  input-field:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "5px 8px"
  cite:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink-2}"
    typography: "{typography.mono}"
    rounded: "{rounded.control}"
    padding: "0 4px"
  rank-selected:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
    height: "22px"
    width: "24px"
---

# Design System: Jev 실험 뷰어

## Overview

**Creative North Star: "The Gazette Comparison Table" (관보 신구조문대비표)**

The viewer is typeset as if it were a page of the 관보 or a statute compilation, not built like an app. It is a white page with near-black ink. Structure comes from horizontal rules: a heavy 2px ink rule opens and closes every table, and fine 1px grey rules divide the cells. Header rows sit on a faint grey ground and are centred. Its central object is the comparison table (대비표). Every condition's answer, evidence, and figures sit side by side against a baseline column. A cell identical to the baseline collapses to "(기준과 같음)". Only what changed is marked, with the statute-blue underline for added material and the red strike for what was dropped or invalid. Difference is the content. Everything else stays quiet so the difference can be read.

Density is high and the tone is clerical. Legal prose (questions, answers, evidence titles, the composer) is set in a Korean myeongjo serif. Everything operational (labels, figures, controls) is set in a sans with tabular numerals. Monospace is reserved for identifiers and hashes. Colour is functional throughout. Three semantic inks carry change, void, and caution. The five experimental conditions are told apart only by tiny square family marks. The world refuses chat bubbles, card-based dashboards, and shadow-lifted panels.

The UI is CSS and inline SVG only, with no raster assets. Fonts are self-hosted (Pretendard Variable and Noto Serif KR variable, both SIL OFL 1.1), so the viewer renders offline.

**Key Characteristics:**
- Rules, not boxes: a 2px ink rule at the top and bottom of every table and list, with 1px grey rules inside.
- Baseline-first comparison: the first column is the baseline, and identical cells collapse to "(기준과 같음)".
- Change is typographic: blue underline for added material and red strike for dropped or invalid material, never fills or badges alone.
- Serif for law, sans for machinery, mono for IDs.
- Condition colour lives only in small marks (8px swatches, 6×10px ticks).
- Missing values render as an em dash with a reason tooltip, never as 0.

## Colors

The palette is ink on paper with grey rules, plus three semantic inks (change blue, void red, note amber), each paired with a soft ground. Three small condition-family hues are used only as marks.

### Primary
- **Gazette Ink** (ink): the text colour, the 2px structural rules, the primary button, the selected rank chip, the tab underline, and the active-row bar in the rail and question list. Ink is both the type and the architecture.

### Secondary
- **Statute Blue** (change): this colour means "differs from the baseline". It marks added words and added evidence (underline 2px, offset 4px), changed config values, and the focus ring. Its soft ground (change-soft) is used for text selection and the "근거 U1" overlap mark.
- **Void Red** (void): failure, invalidity, and removal. It strikes through dropped evidence and invalid citations, and colours failure cells, failed ticks, the error-count tab, and the blocking cost line. Its soft ground (void-soft) backs failure notices and failure marks.

### Tertiary
- **Notice Amber** (note): caution that does not block. It appears as the mock/exploration notice band, "답변 보류", partial-run marks, "답변 생성 중", and the live-API cost line. Its soft ground (note-soft) backs the notice band.

### Condition family marks
- **Vector Grey** (mark-vector), **CE Violet** (mark-ce), **Jev Green** (mark-jev): these identify the condition families vector, CE, and Jev. They appear only as an 8px square swatch before a condition name, as 6×10px ticks in rail and list rows, and in table header cells. FR variants use the same hue as a hollow square (2px inset outline) instead of a filled one.

### Neutral
- **Paper** (paper): page, table, composer, and input ground.
- **Rail Wash** (rail): the left rail's ground, one step off paper.
- **Head Grey** (head): table header rows, the 대비표 row-label column, matrix footers, and plain notices.
- **Hairline** (rule): 1px inner table rules, field strokes, mark outlines, and the rail divider.
- **Soft Hairline** (rule-soft): lighter dividers inside lists and the composer bar, and skeleton bars.
- **Selection Wash** (select): the highlighted matrix row and the current question in the list.
- **Ink 2 / Ink 3** (ink-2, ink-3): secondary text, then tertiary text (metadata keys, sub-labels, "(기준과 같음)", null dashes).

Every colour has a dark-mode counterpart defined on `:root` under `prefers-color-scheme: dark`, which a `data-theme="light"` override can opt out of. Values are in the sidecar. Dark mode keeps the same roles: warm near-black paper (#1b1b1b), light ink (#ececea), and lifted versions of blue, red, and amber.

### Named Rules
**The Difference-Only Rule.** Blue and red mean "differs from baseline" and "dropped, invalid, or failed". Use them nowhere else. Never use them decoratively or as a brand accent.

**The Small Mark Rule.** Condition-family hues never fill a cell, row, column, or button. They appear only as swatches and ticks of 10px or less.

## Typography

**Display / Legal Font:** Noto Serif KR variable (with AppleMyungjo, Nanum Myeongjo, Batang, serif)
**UI Font:** Pretendard Variable (with Apple SD Gothic Neo, Noto Sans KR, system-ui), tabular numerals on the body
**Mono:** ui-monospace / SF Mono / Menlo, for IDs, hashes, chunk locations, config keys and values, and citations only

**Character:** A myeongjo serif carries everything that reads as law or as a question put to the law. A neutral grotesque carries everything that operates the instrument. The contrast between them is the separation of content from machinery.

### Hierarchy
- **Display** (serif 700, 22px, 1.35, -0.02em): page title, such as a run path. The breadcrumb part is ink-3 at weight 400.
- **Headline** (serif 600, 21px, 1.5, -0.015em): the question above a comparison, at most 62ch.
- **Composer** (serif 400, 19px, 1.6): the question input field.
- **Answer** (serif 400, 15px, 1.75): answer text in 대비표 cells. Evidence titles and candidate titles use serif 600 at table size, and rail and question-list entries use serif at 13.5px.
- **Title** (sans 700, 15px, 1.4): section headings, plain text with no marker. Empty-state headings use serif 700 at 17px.
- **Body** (sans 400, 14px, 1.6, tabular): UI default. Tables use 13px.
- **Label** (sans 700, 12.5px): table header cells. The 대비표 row labels ("답 변", "근 거", "수 치") are letter-spaced 0.5em, like the spaced labels of a printed statute table. Header sub-lines ("기준", "≥ 0.12", "제외") are 11.5px weight 400, ink-3.
- **Mono** (11–12px): IDs, hashes, chunk spans, and the cite chips.

### Named Rules
**The Three Voices Rule.** Use serif for legal prose, sans for UI and figures, and mono only for identifiers. Never set an answer in sans, and never set a control in serif.

**The Keep-Words Rule.** Korean prose in narrow table cells uses `word-break: keep-all`, and figure values (`.figs` values) never wrap. Words break at spaces, not mid-syllable-block.

## Layout

The app shell is a fixed 264px left rail plus a fluid main column (`minmax(0, 1fr)`), at full viewport height, with the main column scrolling on its own. Page content is capped at 1400px with 28px top, 40px side, and 72px bottom padding. Section headings get 36px top margin. A hint line appears only where a table needs its notation ("n = 분모 · — = 값 없음"), capped at 78ch. Inside run pages, the question layout is a sticky 240px question list beside the detail, with a 24px gap. Configuration views use auto-fit columns with a 360px minimum.

The 대비표 uses a fixed table layout. The row-label column is 76px, and each condition column has a minimum of 148px, so the table's minimum width is computed as 76 + 148 × the number of conditions. It never squeezes conditions below a readable width. It scrolls horizontally instead.

**Responsive (≤900px):** the shell stacks, with the rail on top (its scroll area capped at 220px) and main below. Page padding drops to 20px 16px 48px. The question list stops being sticky (capped at 280px), two-column grids collapse to one column, the matrix candidate column minimum drops to 200px, and the composer's cost line moves to its own full-width row.

**Table scroll affordance:** every table sits in a wrapper that scrolls horizontally. Background-attachment gradients there draw a soft edge shadow only while columns are hidden off that side.

### Named Rules
**The Full-Measure Table Rule.** The comparison table takes the full content width and scrolls rather than reflowing. Conditions are never stacked into cards on narrow screens.

## Elevation & Depth

The system is flat. Depth comes from ink weight and tonal grounds (paper, rail wash, head grey), never from lift. No surface casts an ambient or drop shadow. The `box-shadow` property appears in only three roles, all of which draw lines rather than elevation:

### Shadow Vocabulary
- **Scroll edge** (`radial-gradient(farthest-side at 0 50%, rgb(0 0 0 / .14), transparent)`, 10px, scroll-attached): shows only when a table has hidden columns to that side.
- **Baseline underline** (`box-shadow: inset 0 -2px 0 var(--ink)`): a 2px ink rule under the baseline column's header cell.
- **Current ring** (`box-shadow: 0 0 0 2px var(--rail), 0 0 0 3px var(--ink)`): an offset 1px ink ring on "새 질문" when it is the current page. Hollow FR swatches and empty ticks use `inset 0 0 0 1.5–2px` outlines in the same line-drawing role.

### Named Rules
**The Ruled-Not-Lifted Rule.** Containment is expressed by 2px ink rules at the top and bottom, never by shadow, floating panels, or card borders on all four sides.

## Shapes

Corners are square. Controls (buttons, inputs, selects, cite chips, rail-foot links) get a barely softened 2px radius. Structural elements (tables, notices, marks, tabs, the composer, rank chips) have no radius. The only circle is the 14px loading spinner. Headings carry no glyph marks. Icons are inline authored SVG on a 20px grid with a 1.5px round-capped stroke (2px at 11px and 16px sizes).

## Components

### Rail
- **Structure:** brand block (serif 17px "Jev 실험 뷰어", no subline) closed by a 2px ink rule. Rail section headings ("탐색 기록", "실행 기록") are plain 12px ink-3 labels. Below it are the "새 질문" primary action, then "탐색 기록" and "실행 기록" sections, then a foot with "설정 비교" and "새로고침" divided by a 1px rule.
- **Items:** a serif title clamped to 2 lines (or a mono run ID), with a meta line of marks, ticks, and time at 11.5px ink-3. Hover is a 4% ink wash. Current is a paper ground with a 2px ink left bar.

### Composer
- **Style:** paper box with a 1px hairline on three sides and a 2px ink rule on top. The serif 19px textarea grows with its content (minimum 92px, maximum 40vh).
- **Bar:** below a soft hairline, the fields "설정", "기준일", and "관할" (12.5px labels, 2px-radius hairline inputs), a spacer, the cost line (ink-3, which turns note amber for live API and void red when blocked), and "질문하기" (⌘/Ctrl+Enter submits; the shortcut lives in the button title, not its label).
- **Focus:** on focus, the box border darkens to ink-3 and the top rule stays ink.

### Primary button
- **Shape:** ink fill, paper text, weight 700, 2px radius, padding 9px 18px.
- **Hover:** the ink is mixed 15% toward statute blue.
- **Disabled:** opacity 0.45 with a not-allowed cursor.
- **Busy:** a 14px paper spinner inside.

### Comparison table (대비표), the signature component
- **Columns:** "구분" label column, then the baseline column (first, CE-R, with sub-label "기준") and the other conditions. The baseline header cell is a slightly darker head grey with a 2px ink underline, and baseline body cells are paper tinted 3% toward ink. Headers name each condition with its family swatch and show any FR threshold ("≥ x") as the sub-line.
- **Rows:** "답변" (serif answer, claims list with cite chips), "근거" (numbered evidence list: serif title plus mono doc and chunk location), and "수치" (a right-aligned figure list of tokens, cost, generation tokens, and timing).
- **Collapse:** a cell identical to the baseline renders "(기준과 같음)", centred serif ink-3. A cell with no generation renders "생성하지 않음". An empty FR selection renders "선택 0개 (문턱값을 넘은 후보 없음)".
- **Marking:** added words and evidence get an underline (2px statute blue, offset 4px, blue text). Dropped baseline evidence is listed with a "−" rank and its title struck through (1.5px void red) in ink-3. Invalid citations are struck through in red. Abstention shows a "답변 보류" note mark plus a short ink-2 explanation.
- **Legend:** one 12px line under the table: "기준 열: CE-R", "(기준과 같음)", a live `<ins>` "추가", and a struck "빠짐". No explanatory prose.

### Candidate matrix
A full-width ruled table of the shared candidate pool. It has a numeric "#" column and a serif candidate title with the snippet clamped to one line (the full text expands on click) and a mono span location. It then has one centred column per condition holding a rank chip. Selected ranks are an ink-filled chip with paper text, and unselected ranks are plain ink-3. Each rank has its raw score under it at 11px. Gold-overlap is marked with a "근거 Ux" change mark. Hovering a row gives a 3% ink wash, and the highlighted row is selection wash. The footer row on head grey totals "선택 수" (and ESR). A legend line follows.

### Marks
Inline 11.5px labels at weight 600: a 1px border, 0 5px padding, square corners. The neutral mark is a hairline on paper. The change, void, and note variants use a 40–45% tinted border, coloured text, and a soft ground. Examples: "15/15행", "mock", "실패 9/9", "답변 보류", "근거 U1".

### Notices
Full-width bands ruled at the top and bottom with a 1px tinted rule (no side borders, no radius). Each has a 17px SVG icon and 13px text with a bold lead phrase, at most 110ch. Variants: note (amber, for mock and live-exploration warnings), void (red, for load and ask failures), and plain (head grey, for exploration-record and skipped-condition information).

### Tabs
A row underlined by a 2px ink rule. Tabs are sans 600 ink-2. The selected tab is ink on paper, boxed in ink on three sides, and breaks through the underline. Counts follow in ink-3 weight 400, and a non-zero "오류" count turns void red and bold.

### Config diff table
Mono 12px key/value rows inside the standard ruled table. Default values are ink-3. A changed value is statute blue with a 1.5px blue underline, and its key goes bold ink. Toolbar checkboxes use ink as the accent colour.

### Question list
A sticky panel ruled 2px ink at the top and bottom, with a sticky filter input. Items show a mono ID with ticks, plus the serif question clamped to 2 lines, separated by soft hairlines. The current item gets selection wash and a 2px ink left bar.

### States
- **Pending:** the 대비표 renders its full grid with grey skeleton bars (100%, 70%, 45% widths) pulsing at 1.1s, plus a progress note ("검색 → 재채점 → 근거 선택 → 생성 중입니다…") and an elapsed timer. Rail lists show 34px skeleton bars.
- **Failure cells:** void red bold stage name ("검색 실패", "재채점 실패", "생성 실패") with a collapsible detail.
- **Empty:** centred block at most 62ch, with a serif 17px heading, ink-2 text, and an optional mono command on paper with a hairline border.
- **Null:** "—" in ink-3, with a title tooltip giving the reason ("값 없음", "비용 미확정: 단가·usage 누락", "미측정").
- **Focus:** a 2px statute-blue outline, offset 2px, on every focusable element.
- **Motion:** colour, background, and opacity transitions of 150ms ease-out only. Skeletons pulse and the spinner spins. `prefers-reduced-motion: reduce` removes all animation and transitions.

## Do's and Don'ts

**The Terse Copy Rule.** Copy is clerical shorthand, like a 관보 table: noun phrases joined with " · " ("mock · 연구 근거 아님", "전체 실패 · 오류 탭 참고", "인덱스 없음 · legal-rag … build-index"). No explanatory sentences under headings, no taglines, no reassurance or caveat prose, no keyboard hints in labels. A notice states the condition and, when needed, the one command that recovers it. Empty states are a heading alone ("오류 없음", "질문 없음").


### Do:
- **Do** open and close every table, list panel, and comparison with a 2px ink rule, and divide its cells with 1px hairline rules.
- **Do** put the baseline condition in the first column and collapse identical cells to "(기준과 같음)".
- **Do** mark added material with the 2px statute-blue underline (offset 4px) and dropped or invalid material with the void-red strike.
- **Do** set questions, answers, evidence titles, and the composer in Noto Serif KR. Set UI and figures in Pretendard with tabular numerals, and IDs in mono.
- **Do** render missing values as an ink-3 "—" with a reason tooltip.
- **Do** keep Korean prose in narrow cells on `word-break: keep-all`, and keep figure values on one line.
- **Do** keep transitions to 150ms ease-out on colour, background, and opacity, and honour reduced motion.

### Don't:
- **Don't** use cards, drop shadows, or four-sided bordered panels as structure. Shadows exist only as scroll-edge cues and line-drawing insets.
- **Don't** render the conversation as chat bubbles or a stacked message feed. A question produces one comparison table.
- **Don't** use condition-family colour beyond swatches, ticks, and header marks. Never fill a column or row with it.
- **Don't** render null, unmeasured, or unpriced values as 0 or $0.
- **Don't** use statute blue or void red for anything other than difference and failure, including brand accents or hover decoration.
- **Don't** set answers or legal text in sans or mono, or set controls in serif.
- **Don't** stack conditions vertically on narrow screens. Let the table scroll horizontally.
