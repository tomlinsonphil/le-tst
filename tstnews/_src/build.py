#!/usr/bin/env python3
"""Build TST News static pages from _src/content.json.

Usage (from anywhere):  python3 tstnews/_src/build.py
Writes: tstnews/index.html, one page per sport (tstnews/<sport id>/index.html),
        tstnews/archive/index.html, tstnews/archive/<date>/... (a dated copy of the same pages),
        tstnews/_src/history/<date>.json (a dated copy of the data, used for "Move" columns).
"""
import re, urllib.parse
import json, os, glob, html, datetime

SRC = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SRC)          # .../tstnews
BASE = '/tstnews'
esc = lambda s: html.escape(str(s), quote=True)

import hashlib
CSSVER = hashlib.md5(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'style.css'), 'rb').read()).hexdigest()[:8]
HEAD = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@75..100,500..800&family=Source+Sans+3:wght@400;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<link rel="stylesheet" href="{base}/style.css?v={ver}">
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
    for sp in data.get('sports', []):
        for g in sp.get('groups', []):
            for p in g.get('panels', []):
                if p.get('title') == title and sp.get('title'):
                    return p
    return None


def links_html(links, label='Read more (free to read)'):
    if not links:
        return ''
    return (f'<div class="links"><h4>{esc(label)}</h4><ul>' + ''.join(
        f'<li><a href="{esc(l["url"])}" target="_blank" rel="noopener">{esc(l["text"])}</a></li>' for l in links) + '</ul></div>')


def community_html(links):
    if not links:
        return ''
    return ('<p class="community">Community: ' + ' · '.join(
        f'<a href="{esc(l["url"])}" target="_blank" rel="noopener">{esc(l["text"])}</a>' for l in links) + '</p>')


ICONS = [
    ('iran', '🌍'), ('ukraine', '🌍'), ('mayoral', '🗳️'), ('leafs', '🏒'), ('jays', '⚾'), ('raptors', '🏀'),
    ('premier', '⚽'), ('ligue', '⚽'), ('champions', '🏆'), ('lower leagues', '⚽'), ('rugby', '🏉'), ('cricket', '🏏'),
    ('tennis', '🎾'), ('squash', '🎾'), ('hockey', '🏑'), ('formula', '🏎️'), ('tesla', '🚗'), ('tech', '💻'),
    ('musk', '🚀'), ('brownlee', '🎬'), ('rogan', '🎙️'), ('carr', '🎤'), ('edgley', '🏊'),
    ('london', '🏛️'), ('windsor', '🏰'), ('bournemouth', '🏖️'), ('finchampstead', '🌳'), ('paris', '🗼'),
    ('sablet', '🍇'), ('vaison', '🏺'), ('orange', '🏟️'), ('avignon', '🌉'), ('tfsa', '🏦'), ('etf', '📈'),
    ('canada', '🍁'), ('united states', '🗽'), ('united kingdom', '💷'), ('china', '🐉'), ('rates', '💹'),
]


def img_html(it, section_id=''):
    im = it.get('img')
    if im and im.get('url'):
        cr = f'<figcaption>{esc(im.get("credit", ""))}</figcaption>' if im.get('credit') else ''
        return f'<figure class="pic"><img src="{esc(im["url"])}" alt="{esc(im.get("alt", it["t"]))}" loading="lazy">{cr}</figure>'
    return ''


def card_html(it, prefix):
    h = [f'<article class="card"><h3>{esc(it["t"])}</h3>{img_html(it)}<span class="tag{" gap" if it.get("gap") else ""}">{esc(it["tag"])}</span>']
    h.append(''.join(f'<p>{esc(p)}</p>' for p in it['w']))
    if it.get('f'):
        h.append('<ul class="facts">' + ''.join(f'<li>{esc(x)}</li>' for x in it['f']) + '</ul>')
    h.append(links_html(it.get('links')))
    if it.get('link'):
        h.append(f'<a class="more" href="{prefix}/{it["link"]}">Full table, results and fixtures →</a>')
    h.append('<div class="guide"><h4>If you\'re new to this</h4>' + ''.join(f'<p>{esc(p)}</p>' for p in it['n']) + '</div>')
    h.append(f'<div class="asof">{esc(it["s"])}</div></article>')
    return ''.join(h)


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


SCORE = re.compile(r'^(?:[^:]*: )?(.+?) (\d+)[–-](\d+) (.+)$')


def hl_link(text):
    m = SCORE.match(text)
    if not m:
        return ''
    q = urllib.parse.quote_plus(f'{m.group(1)} {m.group(4)}')
    return f' <a class="hl-link" href="https://www.youtube.com/@fubotvofficial/search?query={q}">▶ Highlights</a>'


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
        h.append('<ul class="plist">' + ''.join(f'<li>{esc(i)}{hl_link(i) if p.get("highlights") else ""}</li>' for i in p['items']) + '</ul>')
    if p.get('note'):
        h.append(f'<p class="pnote">{esc(p["note"])}</p>')
    h.append(links_html(p.get('links'), 'Source and related (free to read)'))
    h.append('</section>')
    return ''.join(h)


def masthead(data, prefix, current, archive_date, dates):
    secs = [('Headlines', 'headlines'), ('World', 'world'), ('France', 'france'), ('Toronto', 'toronto'), ('UK', 'uk'), ('Tech', 'tech'), ('Following', 'following'), ('Economics', 'money'), ('Sport', 'sport')]
    
    pages = [('Today' if not archive_date else 'Latest', f'{prefix}/', 'home')] + [(n, f'{prefix}/#{i}', 'sec-' + i) for n, i in secs] + [('Quiz', f'{prefix}/quiz/', 'quiz'), ('Archive', f'{BASE}/archive/', 'archive')]
    sportpages = [('Sport', f'{prefix}/#sport', 'sport-home')] + [(sp['title'], f'{prefix}/{sp["id"]}/', sp['id']) for sp in data.get('sports', [])]
    h = ['<header class="mast"><div>']
    h.append(f'<p class="dl">{esc(data["label"])}{" · archive" if archive_date else ""}</p>')
    h.append(f'<h1><a href="{BASE}/">TST News</a></h1></div><button class="theme" id="themeBtn" type="button">Theme: auto</button></header>')
    def navrow(items, label, cls='pages'):
        return f'<nav class="{cls}" aria-label="{label}">' + ''.join(
            f'<a href="{href}"' + (' aria-current="page"' if key == current else '') + f'>{esc(name)}</a>' for name, href, key in items) + '</nav>'
    h.append(navrow(pages, 'Sections', 'pages top') + navrow(sportpages, 'Sport'))
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
    return '' if current in ('home', 'archive') else f'{current}/'


def home_page(data, prefix, archive_date, dates, prev_data):
    h = [HEAD.format(ver=CSSVER, title='TST News', base=BASE), masthead(data, prefix, 'home', archive_date, dates)]
    h.append(f'<p class="note">{esc(data.get("note", ""))}</p>')
    for sec in data['sections']:
        h.append(f'<section class="sec" id="{esc(sec["id"])}"><h2>{esc(sec["title"])}</h2>' + (f'<p class="intro">{esc(sec["intro"])}</p>' if sec.get("intro") else ''))
        h.append(community_html(sec.get('community')))
        if sec.get('kind') == 'papers':
            groups = []
            for pp in sec['papers']:
                if not groups or groups[-1][0] != pp['group']:
                    groups.append((pp['group'], []))
                groups[-1][1].append(pp)
            for gname, lst in groups:
                h.append(f'<h3 class="pgroup">{esc(gname)}</h3><div class="papers">')
                for pp in lst:
                    hd = pp.get('headline')
                    body = (f'<b>{esc(hd)}</b>' + (f'<span>{esc(pp["desc"])}</span>' if pp.get('desc') else '')) if hd else '<span class="nohl">Headline not captured today. Open the front page.</span>'
                    pw = '<em>may need a subscription</em>' if pp.get('paywall') else ''
                    h.append(f'<a class="paper" href="{esc(pp.get("link") or pp["url"])}"><i>{esc(pp["name"])}</i>{body}{pw}</a>')
                h.append('</div>')
            h.append('</section>')
            continue
        if sec.get('kind') == 'feeds':
            h.append('<div class="feeds">')
            for g in sec['feeds']:
                h.append(f'<section class="feed"><h3><a href="{esc(g["url"])}">{esc(g["name"])}</a></h3><ul>' + ''.join(
                    f'<li><a href="{esc(i["url"])}">{esc(i["t"])}</a> <span>{esc(i.get("when", ""))}</span></li>' for i in g['items']) + '</ul></section>')
            h.append('</div></section>')
            continue
        if sec.get('kind') == 'sportlinks':
            h.append('<ul class="tiles">' + ''.join(
                f'<li><a href="{prefix}/{sp["id"]}/"><b>{esc(sp["title"])}</b><span>{esc(sp.get("summary", ""))}</span></a></li>' for sp in data['sports']) + '</ul></section>')
            continue
        if sec['id'] == 'money':
            h.append('<div class="tblwrap econ"><table><thead><tr><th>Country</th><th>Policy rate</th><th>Inflation</th><th>Notes</th></tr></thead><tbody>' + ''.join(
                f'<tr><td><b>{esc(r[0])}</b></td><td class="n">{esc(r[1])}</td><td class="n">{esc(r[2])}</td><td>{esc(r[3])}</td></tr>' for r in data['econ']) + '</tbody></table></div>')
        h.append('<div class="grid">' + ''.join(card_html(it, prefix) for it in sec['items']) + '</div></section>')
    h.append(TAIL)
    return ''.join(h)


def sport_page(data, sport, prefix, archive_date, dates, prev_data):
    h = [HEAD.format(ver=CSSVER, title=f'{sport["title"]} · TST News', base=BASE), masthead(data, prefix, sport['id'], archive_date, dates)]
    h.append(f'<p class="note">{esc(data.get("sport_note", ""))}</p>')
    chips = ([('news', 'News')] if sport.get('cards') else []) + [(g['id'], g.get('short', g['title'])) for g in sport.get('groups', [])]
    if len(chips) > 1:
        h.append('<nav class="rail" aria-label="Sections"><ul>' + ''.join(f'<li><a href="#{esc(i)}">{esc(t)}</a></li>' for i, t in chips) + '</ul></nav>')
    h.append(f'<section class="sec" id="top"><h2>{esc(sport["title"])}</h2><p class="intro">{esc(sport.get("intro", ""))}</p>')
    h.append(community_html(sport.get('community')))
    h.append('</section>')
    if sport.get('cards'):
        h.append('<section class="sec" id="news"><div class="grid">' + ''.join(card_html(it, prefix) for it in sport['cards']) + '</div></section>')
    for g in sport.get('groups', []):
        h.append(f'<section class="sec" id="{esc(g["id"])}"><h2>{esc(g["title"])}</h2><p class="intro">{esc(g.get("intro", ""))}</p><div class="grid panels">')
        h.extend(panel_html(p, prev_data) for p in g['panels'])
        h.append('</div></section>')
    h.append(TAIL)
    return ''.join(h)


def quiz_page(data, prefix, archive_date, dates):
    qz = data['quiz']
    h = [HEAD.format(ver=CSSVER, title='Quiz · TST News', base=BASE), masthead(data, prefix, 'quiz', archive_date, dates)]
    h.append(f'<section class="sec"><h2>{esc(qz["title"])}: {esc(data["label"])}</h2><p class="intro">{esc(qz["intro"])}</p>')
    h.append('<div id="quiz" class="quiz"></div><noscript><p>The quiz needs JavaScript.</p></noscript></section>')
    h.append('<script type="application/json" id="qdata">' + json.dumps(qz['questions'], ensure_ascii=False).replace('</', '<\\/') + '</script>')
    h.append(QUIZJS)
    h.append(TAIL)
    return ''.join(h)


QUIZJS = '''<script>
(function(){
var Q=JSON.parse(document.getElementById('qdata').textContent),box=document.getElementById('quiz'),qs,i,score,locked;
function shuf(a){a=a.slice();for(var k=a.length-1;k>0;k--){var j=Math.floor(Math.random()*(k+1)),t=a[k];a[k]=a[j];a[j]=t}return a}
function el(t,c,x){var e=document.createElement(t);if(c)e.className=c;if(x!==undefined)e.textContent=x;return e}
function start(){qs=shuf(Q).map(function(q){var o=q.options.map(function(t,n){return{t:t,ok:n===q.answer}});return{q:q.q,o:shuf(o),e:q.explain}});i=0;score=0;show()}
function show(){box.textContent='';locked=false;
 if(i>=qs.length){var r=el('div','qres');r.appendChild(el('p','qscore',score+' / '+qs.length));
  var m=score===qs.length?'Perfect score.':score>=qs.length*0.7?'Well read.':score>=qs.length*0.4?'Not bad. Read the cards again.':"Time to read today's stories.";
  r.appendChild(el('p','',m));var b=el('button','qbtn','Start again for the next player');b.onclick=start;r.appendChild(b);box.appendChild(r);return}
 var q=qs[i];box.appendChild(el('p','qmeta','Question '+(i+1)+' of '+qs.length+' · Score '+score));
 box.appendChild(el('h3','qq',q.q));var list=el('div','qopts'),fb=el('p','qfb');
 q.o.forEach(function(op){var b=el('button','qopt',op.t);b.onclick=function(){if(locked)return;locked=true;
  if(op.ok){score++;b.classList.add('good');fb.textContent='Correct. '+q.e}else{b.classList.add('bad');fb.textContent='Not quite. '+q.e;
   Array.prototype.forEach.call(list.children,function(x,n){if(q.o[n].ok)x.classList.add('good')})}
  var nx=el('button','qbtn',i+1>=qs.length?'See my score':'Next question');nx.onclick=function(){i++;show()};box.appendChild(nx)};list.appendChild(b)});
 box.appendChild(list);box.appendChild(fb)}
start()})();
</script>'''


def archive_index(dates, latest):
    data = {'label': 'Every day, kept', 'date': latest}
    h = [HEAD.format(ver=CSSVER, title='Archive · TST News', base=BASE), masthead(data, BASE, 'archive', None, dates)]
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
        write(os.path.join(out, 'quiz', 'index.html'), quiz_page(data, target_prefix, archive_date, dates))
        for sp in data['sports']:
            write(os.path.join(out, sp['id'], 'index.html'), sport_page(data, sp, target_prefix, archive_date, dates, prev_data))
    write(os.path.join(arch, 'index.html'), archive_index(dates, today))
    print('Built', today, 'archive dates:', ', '.join(dates))


if __name__ == '__main__':
    main()
