#!/usr/bin/env python3
"""Build TST News static pages from _src/content.json.

Usage (from anywhere):  python3 tstnews/_src/build.py
Writes: tstnews/index.html, tstnews/football/index.html, tstnews/sport/index.html,
        tstnews/archive/index.html, tstnews/archive/<date>/... (a dated copy of the same pages),
        tstnews/_src/history/<date>.json (a dated copy of the data, used for "Move" columns).
"""
import json, os, glob, html, datetime

SRC = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SRC)          # .../tstnews
BASE = '/tstnews'
esc = lambda s: html.escape(str(s), quote=True)

HEAD = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@75..100,500..800&family=Source+Sans+3:wght@400;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<link rel="stylesheet" href="{base}/style.css">
</head>
<body>
<div class="wrap">
'''
TAIL = '''<footer>
  <p><b>Where to check the facts.</b> Figures come from news reports and official pages gathered on the date shown. Confirm anything you act on at the source. Economics content is general information, not financial advice.</p>
</footer>
</div>
<script>
(function(){var b=document.getElementById('themeBtn'),m=['auto','light','dark'],i=0,r=document.documentElement;
b.addEventListener('click',function(){i=(i+1)%3;if(m[i]==='auto')r.removeAttribute('data-theme');else r.setAttribute('data-theme',m[i]);b.textContent='Theme: '+m[i];});})();
</script>
</body>
</html>
'''


def load(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def find_panel(data, title):
    for key in ('football', 'sport'):
        for g in data.get(key, {}).get('groups', []):
            for p in g.get('panels', []):
                if p.get('title') == title:
                    return p
    return None


def move_cell(team, pos, prev_panel):
    if not prev_panel:
        return '<td class="flat">–</td>'
    prev = {}
    for r in prev_panel.get('rows', []):
        prev[r[prev_panel.get('key', 1)]] = r[0]
    if team not in prev:
        return '<td class="flat">new</td>'
    try:
        d = int(prev[team]) - int(pos)
    except ValueError:
        return '<td class="flat">–</td>'
    if d > 0:
        return f'<td class="up">▲{d}</td>'
    if d < 0:
        return f'<td class="down">▼{-d}</td>'
    return '<td class="flat">–</td>'


def panel_html(p, prev_data):
    h = [f'<section class="panel" id="{esc(p.get("id", ""))}"><h3>{esc(p["title"])}</h3>']
    if p.get('gap'):
        h.append(f'<span class="tag gap">{esc(p.get("tag", "Not verified today"))}</span>')
    h.append(f'<div class="meta">As of {esc(p.get("asof", "n/a"))}' + (f' · Source: {esc(p["source"])}' if p.get('source') else '') + '</div>')
    cols, rows = p.get('cols'), p.get('rows')
    if cols and rows:
        prev_panel = find_panel(prev_data, p['title']) if (p.get('movement') and prev_data) else None
        show_move = bool(p.get('movement') and prev_panel)
        hl = [s.lower() for s in p.get('highlight', [])]
        h.append('<div class="tblwrap"><table><thead><tr>' + ''.join(f'<th>{esc(c)}</th>' for c in cols) + ('<th>Move</th>' if show_move else '') + '</tr></thead><tbody>')
        for r in rows:
            is_hl = any(any(s in str(c).lower() for s in hl) for c in r) if hl else False
            h.append('<tr' + (' class="hl"' if is_hl else '') + '>' + ''.join(
                f'<td class="n">{esc(c)}</td>' if str(c).replace('+', '').replace('-', '').replace(',', '').replace('.', '').isdigit() else f'<td>{esc(c)}</td>' for c in r))
            if show_move:
                h.append(move_cell(r[p.get('key', 1)], r[0], prev_panel))
            h.append('</tr>')
        h.append('</tbody></table></div>')
    if p.get('items'):
        h.append('<ul class="plist">' + ''.join(f'<li>{esc(i)}</li>' for i in p['items']) + '</ul>')
    if p.get('note'):
        h.append(f'<p class="pnote">{esc(p["note"])}</p>')
    h.append('</section>')
    return ''.join(h)


def masthead(data, prefix, current, archive_date, dates):
    pages = [('Today', f'{BASE}/', 'home'), ('Football', f'{prefix}/football/', 'football'), ('Other sport', f'{prefix}/sport/', 'sport'), ('Archive', f'{BASE}/archive/', 'archive')]
    if archive_date:
        pages[0] = ('Latest', f'{BASE}/', 'home')
        pages[0:0] = []
    h = ['<header class="mast"><div>']
    h.append(f'<p class="dl">{esc(data["label"])}{" · archive" if archive_date else ""}</p>')
    h.append(f'<h1><a href="{BASE}/">TST News</a></h1></div><button class="theme" id="themeBtn" type="button">Theme: auto</button></header>')
    h.append('<nav class="pages" aria-label="Pages">' + ''.join(
        f'<a href="{href}"' + (' aria-current="page"' if key == current else '') + f'>{esc(name)}</a>' for name, href, key in pages) + '</nav>')
    # day links
    if archive_date:
        older = [d for d in dates if d < archive_date]
        newer = [d for d in dates if d > archive_date]
        links = []
        if older:
            links.append(f'<a href="{BASE}/archive/{older[0]}/{current_path(current)}">← {older[0]}</a>')
        if newer:
            links.append(f'<a href="{BASE}/archive/{newer[-1]}/{current_path(current)}">{newer[-1]} →</a>')
        links.append(f'<a href="{BASE}/archive/">All dates</a>')
        h.append('<div class="daynav">' + ' '.join(links) + '</div>')
    else:
        older = [d for d in dates if d < data['date']]
        links = []
        for lbl, d in zip(('Yesterday', 'Day before'), older[:2]):
            links.append(f'{lbl}: <a href="{BASE}/archive/{d}/{current_path(current)}">{d}</a>')
        links.append(f'<a href="{BASE}/archive/">All dates</a>')
        h.append('<div class="daynav">' + ' · '.join(links) + '</div>')
    return ''.join(h)


def current_path(current):
    return {'home': '', 'football': 'football/', 'sport': 'sport/'}.get(current, '')


def home_page(data, prefix, archive_date, dates, prev_data):
    h = [HEAD.format(title='TST News', base=BASE), masthead(data, prefix, 'home', archive_date, dates)]
    h.append(f'<p class="note">{esc(data.get("note", ""))}</p>')
    h.append('<nav class="rail" aria-label="Sections"><ul>' + ''.join(
        f'<li><a href="#{esc(s["id"])}">{esc(s.get("short", s["title"]))}</a></li>' for s in data['sections']) + '</ul></nav>')
    for sec in data['sections']:
        h.append(f'<section class="sec" id="{esc(sec["id"])}"><h2>{esc(sec["title"])}</h2><p class="intro">{esc(sec["intro"])}</p>')
        if sec.get('link'):
            h.append(f'<a class="more" href="{prefix}/{sec["link"]["href"]}">{esc(sec["link"]["text"])} →</a>')
        if sec['id'] == 'money':
            h.append('<div class="tblwrap econ"><table><thead><tr><th>Country</th><th>Policy rate</th><th>Inflation</th><th>Notes</th></tr></thead><tbody>' + ''.join(
                f'<tr><td><b>{esc(r[0])}</b></td><td class="n">{esc(r[1])}</td><td class="n">{esc(r[2])}</td><td>{esc(r[3])}</td></tr>' for r in data['econ']) + '</tbody></table></div>')
        h.append('<div class="grid">')
        for it in sec['items']:
            h.append(f'<article class="card"><h3>{esc(it["t"])}</h3><span class="tag{" gap" if it.get("gap") else ""}">{esc(it["tag"])}</span>')
            h.append(''.join(f'<p>{esc(p)}</p>' for p in it['w']))
            if it.get('f'):
                h.append('<ul class="facts">' + ''.join(f'<li>{esc(x)}</li>' for x in it['f']) + '</ul>')
            if it.get('link'):
                h.append(f'<a class="more" href="{prefix}/{it["link"]}">Full table, results and fixtures →</a>')
            h.append('<div class="guide"><h4>If you\'re new to this</h4>' + ''.join(f'<p>{esc(p)}</p>' for p in it['n']) + '</div>')
            h.append(f'<div class="asof">{esc(it["s"])}</div></article>')
        h.append('</div></section>')
    h.append(TAIL)
    return ''.join(h)


def sport_page(data, key, prefix, archive_date, dates, prev_data):
    sec = data[key]
    h = [HEAD.format(title=f'{sec["title"]} · TST News', base=BASE), masthead(data, prefix, key, archive_date, dates)]
    h.append(f'<p class="note">{esc(data.get("sport_note", ""))}</p>')
    h.append('<nav class="rail" aria-label="Sections"><ul>' + ''.join(
        f'<li><a href="#{esc(g["id"])}">{esc(g.get("short", g["title"]))}</a></li>' for g in sec['groups']) + '</ul></nav>')
    for g in sec['groups']:
        h.append(f'<section class="sec" id="{esc(g["id"])}"><h2>{esc(g["title"])}</h2><p class="intro">{esc(g.get("intro", ""))}</p><div class="grid panels">')
        h.extend(panel_html(p, prev_data) for p in g['panels'])
        h.append('</div></section>')
    h.append(TAIL)
    return ''.join(h)


def archive_index(dates, latest):
    data = {'label': 'Every day, kept', 'date': latest}
    h = [HEAD.format(title='Archive · TST News', base=BASE), masthead(data, BASE, 'archive', None, dates)]
    h.append('<section class="sec"><h2>Archive</h2><p class="intro">A copy of each day\'s pages, kept as it was published.</p><ul class="archlist">')
    for d in sorted(dates, reverse=True):
        label = datetime.date.fromisoformat(d).strftime('%A %-d %B %Y')
        h.append(f'<li><a href="{BASE}/archive/{d}/">{esc(label)}</a></li>')
    h.append('</ul></section>')
    h.append(TAIL)
    return ''.join(h)


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)


def main():
    data = load(os.path.join(SRC, 'content.json'))
    today = data['date']
    hist_dir = os.path.join(SRC, 'history')
    os.makedirs(hist_dir, exist_ok=True)
    # previous day's data (latest history file dated before today)
    prev_files = sorted(f for f in glob.glob(os.path.join(hist_dir, '*.json')) if os.path.basename(f)[:-5] < today)
    prev_data = load(prev_files[-1]) if prev_files else None
    # save today's data copy
    write(os.path.join(hist_dir, f'{today}.json'), json.dumps(data, ensure_ascii=False, indent=1))
    # archive dates = existing dated folders + today
    arch = os.path.join(ROOT, 'archive')
    dates = sorted(set([os.path.basename(d) for d in glob.glob(os.path.join(arch, '20??-??-??'))] + [today]))
    for target_prefix, archive_date, out in ((BASE, None, ROOT), (f'{BASE}/archive/{today}', today, os.path.join(arch, today))):
        write(os.path.join(out, 'index.html'), home_page(data, target_prefix, archive_date, dates, prev_data))
        write(os.path.join(out, 'football', 'index.html'), sport_page(data, 'football', target_prefix, archive_date, dates, prev_data))
        write(os.path.join(out, 'sport', 'index.html'), sport_page(data, 'sport', target_prefix, archive_date, dates, prev_data))
    write(os.path.join(arch, 'index.html'), archive_index(dates, today))
    print('Built', today, 'archive dates:', ', '.join(dates))


if __name__ == '__main__':
    main()
