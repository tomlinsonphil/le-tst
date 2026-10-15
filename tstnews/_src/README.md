# TST News: how the pages are made

The site at `le-tst.com/tstnews/` is generated from one data file.

- `content.json` is the only file to edit for a content update.
- `build.py` turns it into static pages: `/tstnews/` (Today), one page per sport (`/tstnews/football/`, `rugby`, `cricket`, `tennis`, `squash`, `field-hockey`, `baseball`, `basketball`, `ice-hockey`, `f1`), `/tstnews/archive/` and a dated copy of every page under `/tstnews/archive/YYYY-MM-DD/`. It also saves the data in `history/YYYY-MM-DD.json`, which it uses for the "Move" column (change in table position since the previous day).
- `../style.css` holds the look. Edit it for design changes.

## Daily update steps

1. `git pull` so you have the latest files.
2. Research the day (see Rules) and edit `content.json`: set `date` (ISO, e.g. `2026-10-12`) and `label` (e.g. `Monday 12 October 2026`), then update every section, item, table, result and fixture.
3. Run `python3 tstnews/_src/build.py` from the repo root.
4. Commit everything under `tstnews/` and push to `main`. GitHub Pages publishes it in a minute or two.

Do not edit generated HTML by hand. Older dated folders under `archive/` are left as they were.

## content.json shape

- `sections[]` (main page, in order): world, toronto, uk, france, sport, tech, following, money. Each has `id`, `title`, `short`, `intro`, optional `community` (links), and `items[]`. The `sport` section has `kind: "sportlinks"` and no items; it shows one tile per entry of `sports[]`.
- Item (a news card): `t` title, `tag` short status, `gap` true when nothing current could be verified, `w` report paragraphs (several, not one line), `f` optional key facts, `n` the "If you're new to this" primer (3 to 5 paragraphs, written for someone who knows nothing about the subject), `s` as-of date and source, `links` (list of `{text, url}`), optional `img` `{url, alt, credit}`.
- `econ[]`: rows of `[country, policy rate, inflation, notes]`.
- `sports[]`: one per sport page. `id` (the URL folder), `title`, `summary` (one line shown on the Today page tile), `intro`, `cards[]` (items as above), `groups[]` (`id`, `title`, `intro`, `panels[]`), `community` (links).
- Panel: `id`, `title`, `asof`, `source`, then either `cols` plus `rows` (a table) or `items` (a list); optional `note`, `links`, `highlight` (substrings to highlight, e.g. `["Bournemouth"]`), `movement` true (adds a Move column; `key` is the index of the team/player column, default 1), and `gap` true with `tag` for panels with nothing verified.

## Rules

- Never invent a figure or a URL. Every number needs a source from the day's research, shown in `asof` and `source`.
- If something cannot be verified, keep the panel and mark it `gap: true` with a clear note. Do not carry yesterday's table forward as if it were today's. If yesterday's figures are reused, say so in `asof`.
- Re-check every date and record in the text ("after 4 games", "3-2-1", "next decision"). Earlier text can be stale.
- Economics content is general information, not financial advice.

## Links (every item that is news should have them)

- Add 1 to 3 `links` per item to stories that are free to read without a subscription. Prefer: BBC, Guardian, CBC, CP24, Global News, CityNews, Al Jazeera, AP, France 24, RFI, Euronews, Public Sénat, official sites (leagues, clubs, central banks, governments, Provence Guide), Wikipedia, and local free-to-read outlets.
- Avoid sites that usually paywall: FT, WSJ, Bloomberg, Telegraph, Times, Toronto Star, Globe and Mail, Le Monde, Le Figaro, La Provence and similar. If a search result or page shows a subscription or registration wall, drop that link.
- Use only URLs that appeared in search results or that you opened and confirmed. If no free story can be found, leave `links` out. Do not guess a URL.
- Local news: look for local outlets (for example for Toronto, Bournemouth, Windsor and the Vaucluse) and the town and tourism sites. Provence Guide lists real local events.
- Community links (`community`): subreddit home pages (for example r/toronto, r/bournemouth, r/leafs). These are fixed links shown under a heading. Reddit posts themselves can be linked only if the URL appeared in search results.
- X, Instagram and Facebook are usually behind login walls and the research tools cannot read them. Do not quote or link individual posts from them unless a search result shows the post text.

## Research tool limits

- WebSearch returns titles and URLs only. WebFetch can read a page only if its URL appeared in search results or was given by the user. Otherwise it asks for permission, and unattended runs get no answer, so the fetch fails.
- Some sites block automated readers (for example some score sites). If a page cannot be read, mark the panel as not verified.

## Useful sources (readable on 11 Oct 2026)

- Premier League and Championship tables, results, fixtures: `footballwebpages.co.uk` (for example `/premier-league/YYYYMMDD`, `/championship/league-table`).
- Ligue 1 table: `eurosport.fr/football/ligue-1/standing.shtml`.
- ATP rankings: `atptour.com/en/rankings/singles`. WTA: `wtatennis.com/rankings/singles` (no date shown, so cross-check).
- F1 standings: `directv.com/insider/f1-standings/` (check which race it is after) and racingnews365.com.
- Maple Leafs record and schedule: `surprisesports.com/scores/nhl/team/maple-leafs-21/`.
- Central banks: bankofcanada.ca, bankofengland.co.uk, federalreserve.gov. Provence events: provenceguide.com. Toronto election: CP24 (`cp24.com`).

## Images and towns

- Every card shows a picture. If an item has `img` (`{url, alt, credit}`) that photo is shown with its credit line; otherwise build.py draws a simple illustration chosen from words in the title (see `ICONS` in build.py).
- Only use a photo when you have confirmed a real, freely licensed file (for example a Wikimedia Commons file page that appeared in search results or that you opened). Use its direct `upload.wikimedia.org` URL and put author and licence in `credit`. Never use news-agency or newspaper photos, and never guess a URL. Keep a photo from day to day for items that continue.
- UK towns followed: London, Windsor, Bournemouth and Finchampstead. Keep all of them (Finchampstead is marked gap when there is no current local news).

## Navigation and highlights

- Top row: Today, World, France, Toronto, UK, Tech, Following, Economics, Archive. Second row: Sport, then one button per sport. Order is set in `masthead()` in build.py. The Economics section has no intro line.
- Football result panels with `"highlights": true` get a "Highlights" link on every result written like `Team A 2–1 Team B`. It opens a YouTube search limited by the words "fubotvofficial" (the FuboTV channel that uploads highlights). Keep results in that format so links appear; set `highlights` on any new football results panel.

## Headlines

`sections[0]` is `headlines` (`kind: "feeds"`, `feeds[]` of `{name, url, items[{t,url,when}]}`). Keep the outlet order: Euronews, CP24, Al Jazeera, Global News, L'Écho du Mardi. Refresh it every day with the latest 4 to 5 stories per outlet, titles and URLs exactly as the feed gives them, never invented. Feeds that worked on 11 Oct 2026 via WebFetch (WebFetch needs the host to have appeared in search results or on a page, so run a quick WebSearch first if a fetch is refused):

- Al Jazeera: `https://www.aljazeera.com/news-sitemap.xml` (UTC times).
- Euronews: `https://www.euronews.com/rss?format=mrss`.
- CP24: `https://www.cp24.com/arc/outboundfeeds/sitemap-news/YYYY-MM-DD/`.
- Global News Toronto: `https://globalnews.ca/toronto/feed/`.
- L'Écho du Mardi (Vaucluse, Avignon): `https://www.echodumardi.com/feed/`.

Blocked or unreadable (do not try to get around it): BBC, Guardian, Le Monde, Figaro, CBC feed, RFI, France 24, CityNews, Bournemouth Echo, Evening Standard, Wokingham Today feed. CTV Windsor is Windsor, Ontario, not Windsor, UK, so do not use it for the UK town. If a feed fails, keep the outlet with the last list and honest dates in `when`, or drop it.

## Images and quiz (updates)

- Cards show a picture only when the item has an `img`. With no photo there is no image and no illustration.
- Quiz page `/tstnews/quiz/`: `content.json` key `quiz` = `{title, intro, questions[]}`, each `{q, options[4], answer (index), explain}`. Every day write about 10 new multiple-choice questions on that day's most relevant stories, using only facts that are in today's content (so each answer is verified). The page shuffles questions and options, shows the score at the end, and "Start again for the next player" restarts it for another family member. The quiz also gets an archive copy for each date.

## Writing voice (all cards)

Write each card's `w` paragraphs like a correspondent filing a piece: open with the hook or the news, a lively verb, a concrete detail, then the "so what". Keep it concise (2 to 3 short paragraphs, no waffle), warm but never gushing, no jokes at anyone's expense, and no first-person filler such as "my searches". Every fact must still come from the day's research; tone never justifies adding a claim. For gap cards, say plainly that nothing current was found, in one lively line. The tone is still being tuned by the reader, so follow any newer instruction recorded here.

## Football highlights and results

- Premier League results should list every match since the last round with its date, taken from footballwebpages.co.uk (`/premier-league/YYYYMMDD`, which lists that day's results and the live table).
- The "Highlights" link on each result opens a search inside the fuboTV Soccer channel (`youtube.com/@fubotvofficial/search?query=...`), because the channel's own video list (page and RSS feed) cannot be read by the research tools. If a real fubo watch URL appears in search results for a match, add it to the item as a `{text,url}` link instead.

## Following list

Following now includes Elon Musk, Marques Brownlee, Joe Rogan, Jimmy Carr, Ross Edgley, Brian Cox, SpaceX, NASA and "Rotten Tomatoes: what's worth watching" (top-rated new films and TV only, not everything released). Sources that were readable: spaceflightnow.com/2026/10/ (SpaceX launches), science.nasa.gov/2026/10/ and nasa.gov news (NASA), editorial.rottentomatoes.com/guide/fresh-movies-2026-ranked/ (RT guide, undated), Brian Cox's Emergence tour pages.

## Menu

Top row (sticky): Today, Headlines, World, France, Toronto, UK, Tech, Following, Economics, Sport, Quiz, Archive. A second row (Sport plus one button per sport) scrolls away. The round section chips on Today were removed. Menu code is `masthead()` in build.py.

## Link synopses (toggle)

Any link in a card's `links` or any Headlines feed item may carry an optional `syn` (1 to 2 sentences, max about 45 words, neutral, written only from the page actually read). build.py shows a small "Synopsis ▾" toggle after the link that reveals it. No `syn` means no toggle. Never write a synopsis for a page you could not read; skipping is fine. Synopses are written fresh for each day's new links; older links keep theirs.
