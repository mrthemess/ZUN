"""Widoczność w Google: adres kanoniczny i wersje językowe (hreflang), dane strukturalne
(LearningResource), sekcja „O narzędziu” ze stałym tekstem oraz sitemap.xml z wersjami PL/EN.

Uruchomienie (z folderu strony): python3 skrypty/seo.py
Dane narzędzi (nazwy, opisy, listy) bierze z tablicy TOOLS na stronie głównej, a pytania
i odpowiedzi z seo_teksty.py. Można puszczać wielokrotnie – zastępuje poprzednie bloki.

Narzędzia przełączają język parametrem ?lang=en, więc wersja angielska ma osobny adres.
Adres kanoniczny i hreflang ustawia skrypt w <head>, bo zależą od parametrów adresu
(?lang=en, ?czesc=czas, ?przedmiot=bio, ?tryb=generator). Google wykonuje JavaScript,
a sitemap podaje te same pary PL/EN bez potrzeby uruchamiania skryptu.
"""
import datetime, html, json, pathlib, re, subprocess, sys, tempfile

from seo_teksty import FAQ

# bez argumentu: repozytorium strony, w którym leży ten skrypt
root = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parent.parent
SITE = 'https://narzedzia.netlify.app/'
TODAY = datetime.date.today().isoformat()
AUTHOR = {'@type': 'Person', 'name': 'Bartłomiej Wrona'}
LICENSE = 'https://creativecommons.org/licenses/by-nc-sa/4.0/'

# ---------- dane z TOOLS (JavaScript wykonany przez osascript, bez Node) ----------
idx = (root / 'index.html').read_text(encoding='utf-8')
m = re.search(r'const TOOLS = (\[.*?\n\]);', idx, re.S)
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as t:
    t.write('var TOOLS = ' + m.group(1) + ';JSON.stringify(TOOLS)')
TOOLS = json.loads(subprocess.run(['osascript', '-l', 'JavaScript', t.name], capture_output=True, text=True, check=True).stdout)

# wykresy-i-tabele.html bez parametru: wersja łączona (geografia + biologia)
WYK = {'id': 'wykresy', 's': 'both', 'file': 'wykresy-i-tabele.html', 'lang': 'full',
       'pl': ['Wykresy i tabele', 'Trener czytania wykresów i tabel z biologii i geografii: odczytywanie wartości z jednej i dwóch osi, porównania, obliczenia i wnioski.',
              ['wykres z dwiema osiami krok po kroku', 'ćwiczenia na trzech poziomach: odczyt, porównania, obliczenia', 'procenty a punkty procentowe, promile, amplitudy', 'zadania „prawda/fałsz” jak na konkursach']],
       'en': ['Charts and tables', 'A trainer for reading charts and tables in biology and geography: reading values from one and two axes, comparing, calculating and drawing conclusions.',
              ['dual-axis charts step by step', 'practice at three levels: reading, comparing, calculating', 'percent vs percentage points, per mille, ranges', 'true/false statements like in contests']]}
FAQ['wykresy'] = FAQ['wykresy-geo'] + FAQ['wykresy-bio']


def variants():
    """plik -> lista wariantów; pierwszy to wersja bez parametrów"""
    by = {}
    for t in TOOLS + [WYK]:
        q, match = '', None
        if t.get('g'):
            q, match = 'tryb=generator', ['tryb', 'generator']
        elif t.get('q'):
            q = t['q'].lstrip('&')
            match = q.split('=')
        by.setdefault(t['file'], []).append({'t': t, 'q': q, 'm': match, 'k': t['id'], 'en': t['lang'] != 'contest'})
    for f, vs in by.items():
        vs.sort(key=lambda v: v['m'] is not None)  # wersja podstawowa na początek
        assert vs[0]['m'] is None, f
    return by


def url(file, q, en):
    ps = (['lang=en'] if en else []) + ([q] if q else [])
    return SITE + file + ('?' + '&'.join(ps) if ps else '')


def ld(v, en):
    t = v['t']; L = 'en' if en else 'pl'; name, desc = t[L][0], t[L][1]
    gen = v['q'] == 'tryb=generator'
    subj = {'geo': ['Geografia', 'Geography'], 'bio': ['Biologia', 'Biology'], 'both': ['Geografia i biologia', 'Geography and biology']}[t['s']][en]
    o = {'@context': 'https://schema.org', '@type': 'LearningResource',
         'name': (('Generator kart pracy: ' if not en else 'Worksheet generator: ') + name) if gen else name,
         'description': desc, 'url': url(t['file'], v['q'], en), 'inLanguage': L,
         'learningResourceType': ('worksheet' if gen else 'interactive resource'),
         'educationalLevel': ['szkoła podstawowa', 'liceum'] if not en else ['primary school', 'secondary school'],
         'audience': {'@type': 'EducationalAudience', 'educationalRole': 'teacher' if gen else 'student'},
         'about': {'@type': 'Thing', 'name': subj},
         'isAccessibleForFree': True, 'author': AUTHOR,
         'isPartOf': {'@type': 'WebSite', 'name': 'Zakład utylizacji niewiedzy', 'url': SITE}}
    if v['en']:
        o['license'] = LICENSE  # zadania konkursowe nie są na licencji CC
    return o


def head_block(file, vs):
    data = [{'k': v['k'], 'q': v['q'], 'm': v['m'], 'en': v['en'],
             'd': [v['t']['pl'][1], v['t']['en'][1]], 'ld': [ld(v, False), ld(v, True) if v['en'] else None]} for v in vs]
    js = ("(function(){var V=" + json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/') + ",B=" + json.dumps(SITE + file) + ","
          "p=new URLSearchParams(location.search),v=V[0],h=document.head,i;"
          "for(i=1;i<V.length;i++)if(p.get(V[i].m[0])===V[i].m[1]){v=V[i];break}"
          "var en=v.en&&p.get('lang')==='en';document.documentElement.setAttribute('data-seo',v.k);"
          "function u(l){var q=[];if(l)q.push('lang=en');if(v.q)q.push(v.q);return B+(q.length?'?'+q.join('&'):'')}"
          "function ln(r,x,hl){var e=document.createElement('link');e.rel=r;e.href=x;if(hl)e.hreflang=hl;h.appendChild(e)}"
          "ln('canonical',u(en));if(v.en){ln('alternate',u(0),'pl');ln('alternate',u(1),'en');ln('alternate',u(0),'x-default')}"
          "var m=document.querySelector('meta[name=description]');if(m)m.content=v.d[en?1:0];"
          "var j=document.getElementById('seo-ld');if(j)j.textContent=JSON.stringify(v.ld[en?1:0]);})();")
    static_ld = json.dumps(ld(vs[0], False), ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    return f'<!--seo2--><script type="application/ld+json" id="seo-ld">{static_ld}</script><script>{js}</script><!--seo2-->'


def section(file, vs):
    e = html.escape
    home = '../index.html' if '/' in file else 'index.html'
    css = ("#o-narzedziu{max-width:1180px;margin:0 auto;padding:28px 16px 120px;font:16px/1.6 'Atkinson Hyperlegible',system-ui,sans-serif;color:inherit;position:relative;z-index:0}"
           "#o-narzedziu>div{border-top:1.5px solid rgba(128,128,128,.35);padding-top:18px}"
           "#o-narzedziu h2{font:800 1.3rem/1.2 'Bricolage Grotesque','Atkinson Hyperlegible',sans-serif;margin:0 0 8px}"
           "#o-narzedziu h3{font:700 1.02rem/1.3 'Atkinson Hyperlegible',sans-serif;margin:16px 0 6px}"
           "#o-narzedziu p,#o-narzedziu li,#o-narzedziu dd{opacity:.88}#o-narzedziu p{margin:0 0 8px}#o-narzedziu ul{margin:0;padding-left:20px}"
           "#o-narzedziu dl{margin:0}#o-narzedziu dt{font-weight:700;margin-top:10px}#o-narzedziu dd{margin:2px 0 0}"
           "#o-narzedziu a{color:inherit;font-weight:700}#o-narzedziu .m{font-size:.9rem;margin-top:16px}"
           "html[lang=en] #o-narzedziu [lang=pl],html:not([lang=en]) #o-narzedziu [lang=en]{display:none}"
           "@media print{#o-narzedziu{display:none}}"
           + ''.join(f'html[data-seo="{v["k"]}"] #o-narzedziu [data-v]:not([data-v="{v["k"]}"]){{display:none}}' for v in vs))
    out = []
    for v in vs:
        t = v['t']; gen = v['q'] == 'tryb=generator'
        for L in (['pl', 'en'] if v['en'] else ['pl']):
            pl = L == 'pl'; name, desc, items = t[L]
            h2 = (('Generator kart pracy: ' if pl else 'Worksheet generator: ') + name) if gen else (('O narzędziu: ' if pl else 'About this tool: ') + name)
            s = f'<div data-v="{v["k"]}" lang="{L}"><h2>{e(h2)}</h2><p>{e(desc)}</p>'
            s += f'<h3>{"Co tu znajdziesz" if pl else "What is inside"}</h3><ul>' + ''.join(f'<li>{e(x)}</li>' for x in items) + '</ul>'
            qa = [] if gen else FAQ.get(t['id'], [])
            qa = [(a, b) if pl else (c, d) for a, b, c, d in qa if (a if pl else c)]
            if qa:
                s += f'<h3>{"Najczęstsze pytania" if pl else "Common questions"}</h3><dl>' + ''.join(f'<dt>{e(q)}</dt><dd>{e(a)}</dd>' for q, a in qa) + '</dl>'
            if gen:
                lesson = file.rsplit('/', 1)[-1]
                s += (f'<p class="m">{"Karta pracy do pobrania w Wordzie (.docx) albo do wydruku, z kluczem odpowiedzi na osobnej stronie. Wersja dla uczniów:" if pl else "A worksheet to download as a Word file (.docx) or print, with the answer key on a separate page. Student version:"} '
                      f'<a href="{lesson}{"" if pl else "?lang=en"}">{e(name)}</a>.</p>')
            s += (f'<p class="m">{"Darmowe narzędzie do nauki dla szkoły podstawowej i liceum – bez logowania i bez reklam. Autor: Bartłomiej Wrona, nauczyciel geografii i biologii." if pl else "A free learning tool for primary and secondary school – no sign-up and no ads. Made by Bartłomiej Wrona, a geography and biology teacher."} '
                  f'<a href="{home}?lang={L}">{"Wszystkie narzędzia" if pl else "All tools"}</a>.</p></div>')
            out.append(s)
    return f'<!--o-narzedziu--><style>{css}</style><section id="o-narzedziu" aria-label="O narzędziu / About this tool">' + ''.join(out) + '</section><!--o-narzedziu-->'


CANON = re.compile(r'<link rel="canonical" href="[^"]*">')
BLOCK = lambda n: re.compile(rf'<!--{n}-->.*?<!--{n}-->', re.S)
by = variants()

for file, vs in by.items():
    f = root / file
    s = f.read_text(encoding='utf-8')
    s = BLOCK('seo2').sub('', s); s = BLOCK('o-narzedziu').sub('', s)
    s = CANON.sub('', s)
    hb = head_block(file, vs)
    a = s.index('<!--seo-->', s.index('<!--seo-->') + 1) + len('<!--seo-->')  # po meta description, które skrypt podmienia
    s = s[:a] + hb + s[a:]
    b = s.index('<style>#site-bar')
    s = s[:b] + section(file, vs) + s[b:]
    f.write_text(s, encoding='utf-8')
    print('ok', file, [v['k'] for v in vs])

# ---------- strona główna ----------
HOME_D = ['Darmowe interaktywne narzędzia do nauki geografii i biologii: współrzędne geograficzne, skala mapy, poziomice, klimatogramy, mapa pogody, Układ Słoneczny, genetyka, klucz do oznaczania gatunków i więcej. Także po angielsku.',
          'Free interactive tools for learning geography and biology: geographic coordinates, map scale, contour lines, climographs, weather maps, the Solar System, genetics, an identification key and more. Also in Polish.']
s = BLOCK('seo2').sub('', idx)
s = CANON.sub('', s)
js = ("(function(){var en=new URLSearchParams(location.search).get('lang')==='en',h=document.head,B=" + json.dumps(SITE) + ",D=" + json.dumps(HOME_D, ensure_ascii=False) + ";"
      "function ln(r,x,hl){var e=document.createElement('link');e.rel=r;e.href=x;if(hl)e.hreflang=hl;h.appendChild(e)}"
      "ln('canonical',en?B+'?lang=en':B);ln('alternate',B,'pl');ln('alternate',B+'?lang=en','en');ln('alternate',B,'x-default');"
      "if(en){var m=document.querySelector('meta[name=description]');if(m)m.content=D[1]}})();")
a = s.index('>', s.index('<meta name="description"')) + 1
s = s[:a] + f'<!--seo2--><script>{js}</script><!--seo2-->' + s[a:]
(root / 'index.html').write_text(s, encoding='utf-8')
print('ok index.html')

# ---------- sitemap ----------
rows = []
def entry(loc, alts, pr):
    x = f'  <url><loc>{html.escape(loc)}</loc><lastmod>{TODAY}</lastmod><priority>{pr}</priority>'
    for hl, h in alts:
        x += f'<xhtml:link rel="alternate" hreflang="{hl}" href="{html.escape(h)}"/>'
    return x + '</url>'
alts = [('pl', SITE), ('en', SITE + '?lang=en'), ('x-default', SITE)]
rows += [entry(SITE, alts, '1.0'), entry(SITE + '?lang=en', alts, '0.9')]
for file, vs in by.items():
    for v in vs:
        pr = '0.6' if v['q'] == 'tryb=generator' else '0.8'
        pl, en = url(file, v['q'], False), url(file, v['q'], True)
        if v['en']:
            a2 = [('pl', pl), ('en', en), ('x-default', pl)]
            rows += [entry(pl, a2, pr), entry(en, a2, pr)]
        else:
            rows.append(entry(pl, [], pr))
(root / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + '\n'.join(rows) + '\n</urlset>\n', encoding='utf-8')
print('sitemap', len(rows), 'adresów')
