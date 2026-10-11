# TST News: how the pages are made

The site at `le-tst.com/tstnews/` is generated from one data file.

- `content.json` is the only file to edit for a content update. It holds today's date, the main-page sections, the economics table, and the Football and Other sport pages (groups of "panels").
- `build.py` turns `content.json` into static pages: `/tstnews/` (Today), `/tstnews/football/`, `/tstnews/sport/`, `/tstnews/archive/` and a dated copy under `/tstnews/archive/YYYY-MM-DD/`. It also saves a copy of the data in `history/YYYY-MM-DD.json`, which it uses to work out the "Move" column (change in table position since the previous day).
- `../style.css` holds the look. Edit it for design changes.

## Daily update steps

1. `git pull` so you have the latest files.
2. Research the day (see "Rules" below) and edit `content.json`: set `date` (ISO, e.g. `2026-10-12`) and `label` (e.g. `Monday 12 October 2026`), then update every section item, table, result and fixture.
3. Run `python3 tstnews/_src/build.py` from the repo root.
4. Commit everything under `tstnews/` and push to `main`. GitHub Pages publishes it in a minute or two.

Do not edit the generated HTML by hand. It is rewritten on every build. Older dated folders under `archive/` are left as they were.

## content.json shape

- `sections[]`: `id`, `title`, `short`, `intro`, optional `link` `{href, text}`, and `items[]`.
- Item: `t` (title), `tag` (short status), `gap` (true when nothing current could be verified), `w` (report paragraphs), `f` (optional key facts), `n` (the "If you're new to this" primer, 3 to 5 paragraphs), `s` (as-of date and source), optional `link` (for example `football/#premier-league`).
- `econ[]`: rows of `[country, policy rate, inflation, notes]`.
- `football` and `sport`: `groups[]` with `id`, `title`, `intro`, `panels[]`.
- Panel: `id`, `title`, `asof`, `source`, then either `cols` plus `rows` (a table) or `items` (a list), optional `note`, `highlight` (substrings to highlight, such as `["Bournemouth"]`), `movement` true (adds a Move column; `key` is the index of the team column, default 1), and `gap` true with `tag` for panels with nothing verified.

## Rules

- Never invent a figure. Every number needs a source from the day's research, shown in `asof` and `source`.
- If something cannot be verified, keep the panel and mark it `gap: true` with a clear note. Do not carry yesterday's table forward as if it were today's. If yesterday's figures are reused, say so in `asof`.
- Dates and records change daily, so re-check every "as of" line, including text such as "after 4 games", "3-2-1" or "next decision".
- Economics content is general information, not financial advice.
- Keep the primers (`n`) fresh in substance but they can stay the same from day to day unless the story changes.

## Useful sources (public pages the research tools could read on 11 Oct 2026)

- Premier League and Championship tables, results, fixtures: `footballwebpages.co.uk` (for example `/premier-league/YYYYMMDD`, `/championship/league-table`).
- Ligue 1 table: `eurosport.fr/football/ligue-1/standing.shtml`.
- ATP rankings: `atptour.com/en/rankings/singles`. WTA: `wtatennis.com/rankings/singles` (the page does not show a date, so cross-check).
- F1 standings: `directv.com/insider/f1-standings/` (check which race it is after) and racingnews365.com.
- Maple Leafs record and schedule: `surprisesports.com/scores/nhl/team/maple-leafs-21/`.
- Central banks: bankofcanada.ca, bankofengland.co.uk, federalreserve.gov. Provence events: provenceguide.com.
- Some sites block automated readers. If a page cannot be read, mark the panel as not verified.
