"""Wstawia pasek na dole każdego narzędzia: powrót do strony głównej, kod QR,
tryb rzutnika, przełącznik jasny/ciemny i „Zgłoś błąd”. Do <head> każdej strony
(także index.html i 404.html) wstawia skrypt, który przed narysowaniem strony
ustawia zapamiętany motyw (data-theme na <html>, klucz zunMotyw w localStorage).
Uruchomienie (z folderu strony): python3 skrypty/pasek.py

Zastępuje poprzedni pasek (od <a id="home-link" do końca jego <script>),
więc można go puszczać wielokrotnie. Narzędzia z własnym przełącznikiem PL/EN
(rozpoznawane po MutationObserver w starym pasku) dostają napisy podążające
za atrybutem lang na <html>; pozostałe biorą język ze strony głównej.
"""
import pathlib, re, sys

# bez argumentu: repozytorium strony, w którym leży ten skrypt
root = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parent.parent
SKIP = {'index.html', '404.html'}

def dark_rules(css):
    """Te same reguły dla ciemnego motywu systemowego (o ile nie wybrano jasnego) i dla wybranego ciemnego."""
    import re as _re
    def pre(prefix):
        return _re.sub(r'(^|})([^{}]+)\{', lambda m: m.group(1) + ','.join(prefix + x for x in m.group(2).split(',')) + '{', css)
    return ('@media (prefers-color-scheme:dark){' + pre(':root:not([data-theme=light]) ') + '}' + pre(':root[data-theme=dark] '))


STYLE = (
    "<style>"
    # all:unset odcina style narzędzia (każde ma własne reguły dla a i button), więc pasek wygląda wszędzie tak samo
    "#site-bar,#site-bar a,#site-bar button,#site-bar span,#report-link,#report-link span{all:unset;box-sizing:border-box}"
    "#site-bar{position:fixed;left:14px;bottom:14px;z-index:9999;display:flex;gap:4px;align-items:center;padding:5px;"
    "background:rgba(253,252,248,.92);border:1px solid rgba(35,31,23,.14);border-radius:999px;"
    "box-shadow:0 6px 24px rgba(0,0,0,.22);-webkit-backdrop-filter:blur(8px);backdrop-filter:blur(8px)}"
    "#site-bar a,#site-bar button,#report-link{display:inline-flex;align-items:center;gap:8px;min-height:44px;padding:0 16px;"
    "border-radius:999px;cursor:pointer;font:700 15px/1 'Atkinson Hyperlegible',system-ui,sans-serif;color:#231f17;"
    "white-space:nowrap;transition:background .15s,transform .15s,box-shadow .15s}"
    "#site-bar svg{display:block;width:20px;height:20px;flex:none;fill:none;stroke:currentColor;stroke-width:2.2;stroke-linecap:round;stroke-linejoin:round}"
    "#site-bar #home-link{background:#231f17;color:#fdfcf8!important;padding:0 18px 0 14px!important}"
    "#site-bar #home-link:hover{background:#3a3326;transform:translateY(-1px)}"
    "#site-bar button:hover{background:rgba(35,31,23,.08)}"
    "#site-bar button[aria-pressed=true]{background:#e2b27a}"
    "#site-bar a:focus-visible,#site-bar button:focus-visible,#report-link:focus-visible{outline:3px solid #2f6fbf;outline-offset:2px}"
    "#report-link{position:fixed;right:14px;bottom:14px;z-index:9999;font-size:14px;background:rgba(253,252,248,.92);"
    "border:1px solid rgba(35,31,23,.14);box-shadow:0 6px 24px rgba(0,0,0,.18);-webkit-backdrop-filter:blur(8px);backdrop-filter:blur(8px)}"
    "#report-link:hover{transform:translateY(-1px)}"
    + dark_rules(
        "#site-bar,#report-link{background:rgba(30,27,21,.92);border-color:rgba(236,230,218,.18)}"
        "#site-bar button,#report-link{color:#ece6da}#site-bar button:hover{background:rgba(236,230,218,.1)}"
        "#site-bar #home-link{background:#e2b27a;color:#1a140c!important}#site-bar #home-link:hover{background:#ecc391}"
        "#site-bar button[aria-pressed=true]{background:#e2b27a;color:#1a140c}"
    ) +
    # przewijanie do elementu (scrollIntoView, fokus) zostawia miejsce na pasek, żeby wyniki nie chowały się pod nim
    "html{scroll-padding-bottom:96px}html.rzutnik{scroll-padding-bottom:124px}"
    # QR i rzutnik przydają się przy tablicy, nie na telefonie; motyw zostaje jako sama ikona
    "#site-bar #home-link .s{display:none}"
    "@media (max-width:760px){#site-bar #home-link .t{display:none}#site-bar #home-link .s{display:inline}#site-bar button:not(#theme-btn){display:none}#site-bar #theme-btn{padding:0 12px}#site-bar #theme-btn .t{display:none}#site-bar{padding:4px}#report-link .t{display:none}#report-link{padding:0 14px}}"
    "@media print{#site-bar,#report-link,#qr-dlg{display:none!important}}"
    "html.rzutnik body{zoom:1.3}"
    "#qr-dlg{position:fixed;inset:0;z-index:10000;background:rgba(15,18,14,.75);display:grid;place-items:center;padding:16px}"
    "#qr-dlg>div{background:#fff;color:#111;border-radius:20px;padding:24px;text-align:center;max-width:94vw;"
    "font:400 16px/1.4 'Atkinson Hyperlegible',system-ui,sans-serif}"
    "#qr-dlg h2{margin:0 0 4px;font:800 1.6rem/1.2 'Bricolage Grotesque','Atkinson Hyperlegible',sans-serif}"
    "#qr-dlg .qr{display:grid;place-items:center;margin:14px auto}"
    "#qr-dlg .qr img,#qr-dlg .qr canvas{width:min(62vh,80vw,560px)!important;height:auto!important;image-rendering:pixelated}"
    "#qr-dlg .u{word-break:break-all;color:#555;font-size:.9rem;margin:0 0 14px}"
    "#qr-dlg button{font:700 1rem 'Atkinson Hyperlegible',sans-serif;cursor:pointer;border:1.5px solid #dcd4c3;background:#fdfcf8;"
    "color:#231f17;border-radius:12px;padding:10px 18px}"
    "</style>"
)



# ikony rysowane kreską (stroke), kolor z napisu
ICON_HOME = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M19 12H5"/><path d="m11 6-6 6 6 6"/></svg>'
ICON_MOON = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z"/></svg>'
ICON_SUN = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M5.3 18.7l1.4-1.4M17.3 6.7l1.4-1.4"/></svg>'

# ustawia zapamiętany motyw zanim strona się narysuje (bez mignięcia)
HEAD = ('<script id="zun-motyw">try{var m=localStorage.getItem(\'zunMotyw\');'
        'if(m===\'dark\'||m===\'light\')document.documentElement.setAttribute(\'data-theme\',m)}catch(e){}</script>')
HEAD_RE = re.compile(r'<script id="zun-motyw">.*?</script>', re.S)
ICON_QR = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3.5" y="3.5" width="6.5" height="6.5" rx="1"/><rect x="14" y="3.5" width="6.5" height="6.5" rx="1"/><rect x="3.5" y="14" width="6.5" height="6.5" rx="1"/><path d="M14 14h2.5v2.5H14zM18 18h2.5v2.5H18zM14 20.5h1.5M20.5 14v1.5"/></svg>'
ICON_PROJ = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="4" width="18" height="12" rx="1.5"/><path d="M8 20h8M12 16v4"/></svg>'

def bar(home, rel, follows_html_lang):
    script = (
        "<script>(function(){"
        "var a=document.getElementById('home-link'),r=document.getElementById('report-link'),"
        "qb=document.getElementById('qr-btn'),pb=document.getElementById('proj-btn'),tb=document.getElementById('theme-btn'),h=document.documentElement,"
        "mq=matchMedia('(prefers-color-scheme: dark)'),"
        "p=new URLSearchParams(location.search),l=p.get('lang'),X='pl';"
        # generator, rachuba czasu i wykresy z geografii/biologii to osobne pozycje w formularzu zgłoszeń
        "var q=(p.get('tryb')==='generator'?'&tryb=generator':'')+(p.get('czesc')==='czas'?'&czesc=czas':'')"
        "+(/^(geo|bio)$/.test(p.get('przedmiot'))?'&przedmiot='+p.get('przedmiot'):'');"
        "try{l=l||localStorage.getItem('siteLang')}catch(e){}"
        # motyw: wybór zapisany w zunMotyw (wspólny dla wszystkich narzędzi), bez wyboru – ustawienie systemu
        "function dk(){var t=h.getAttribute('data-theme');return t?t==='dark':mq.matches}"
        f"function th(){{if(!tb)return;var d=dk(),e=X==='en';tb.firstChild.outerHTML=d?'{ICON_SUN}':'{ICON_MOON}';"
        "tb.lastChild.textContent=d?(e?'Light mode':'Tryb jasny'):(e?'Dark mode':'Tryb ciemny');"
        "tb.title=d?(e?'Switch to light mode':'Przełącz na tryb jasny'):(e?'Switch to dark mode':'Przełącz na tryb ciemny');tb.setAttribute('aria-label',tb.title)}"
        "if(tb)tb.onclick=function(){var m=dk()?'light':'dark';h.setAttribute('data-theme',m);try{localStorage.setItem('zunMotyw',m)}catch(e){}"
        "th();dispatchEvent(new CustomEvent('zun-motyw',{detail:m}))};"
        "try{mq.addEventListener('change',th)}catch(e){}"
        "function s(x){X=x=x==='en'?'en':'pl';var e=x==='en';"
        "a.children[1].textContent=e?'Back to all tools':'Wróć do wszystkich narzędzi';a.lastChild.textContent=e?'All tools':'Wszystkie narzędzia';a.title=e?'Go back to the list of all tools':'Wróć do strony głównej z listą wszystkich narzędzi';"
        f"a.href='{home}?lang='+x;"
        "r.lastChild.textContent=e?'Report a bug':'Zgłoś błąd';"
        f"r.href='{home}?lang='+x+'&zglos={rel}'+q;"
        "qb.lastChild.textContent=e?'QR code':'Kod QR';qb.title=e?'Show a QR code for this tool':'Pokaż kod QR do tego narzędzia';"
        "pb.lastChild.textContent=e?'Projector':'Rzutnik';pb.title=e?'Enlarge everything for the classroom screen':'Powiększ wszystko do wyświetlania na tablicy';th()}"
        + ("s(h.lang);new MutationObserver(function(){s(h.lang)}).observe(h,{attributes:true,attributeFilter:['lang']});"
           if follows_html_lang else "s(l);")
        # tryb rzutnika: zapamiętany dla wszystkich narzędzi
        + "function proj(on){h.classList.toggle('rzutnik',on);pb.setAttribute('aria-pressed',on);try{localStorage.setItem('zunRzutnik',on?'1':'')}catch(e){}}"
        "var on=false;try{on=localStorage.getItem('zunRzutnik')==='1'}catch(e){}proj(on);"
        "pb.onclick=function(){proj(!h.classList.contains('rzutnik'))};"
        # kod QR: ten sam adres w bieżącym języku, zawsze wersja dla uczniów (bez trybu generatora)
        "function qr(){var e=X==='en',u=new URL(location.href.split('#')[0]);u.searchParams.delete('tryb');u.searchParams.set('lang',X);"
        "var d=document.createElement('div');d.id='qr-dlg';d.setAttribute('role','dialog');d.setAttribute('aria-modal','true');"
        "d.innerHTML='<div><h2></h2><p>'+(e?'Scan with your phone camera':'Zeskanuj aparatem telefonu')+'</p><div class=\"qr\"></div><p class=\"u\"></p><button type=\"button\">'+(e?'Close':'Zamknij')+'</button></div>';"
        "d.querySelector('h2').textContent=document.title;d.querySelector('.u').textContent=u.href;"
        "function close(){d.remove();document.removeEventListener('keydown',k)}function k(ev){if(ev.key==='Escape')close()}"
        "d.onclick=function(ev){if(ev.target===d||ev.target.tagName==='BUTTON')close()};document.addEventListener('keydown',k);"
        "document.body.append(d);d.querySelector('button').focus();"
        "function draw(){new QRCode(d.querySelector('.qr'),{text:u.href,width:560,height:560,correctLevel:QRCode.CorrectLevel.M})}"
        "if(window.QRCode)return draw();var sc=document.createElement('script');"
        "sc.src='https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js';sc.onload=draw;"
        "sc.onerror=function(){d.querySelector('.qr').textContent=e?'No internet connection – the QR code could not be loaded.':'Brak internetu – nie udało się wczytać kodu QR.'};"
        "document.head.append(sc)}"
        "qb.onclick=qr;"
        "})();</script>"
    )
    return (
        STYLE
        + f'<div id="site-bar"><a id="home-link" href="{home}">{ICON_HOME}<span class="t">Wróć do wszystkich narzędzi</span><span class="s">Wszystkie narzędzia</span></a>'
        f'<button type="button" id="qr-btn">{ICON_QR}<span class="t">Kod QR</span></button>'
        f'<button type="button" id="proj-btn" aria-pressed="false">{ICON_PROJ}<span class="t">Rzutnik</span></button>'
        f'<button type="button" id="theme-btn">{ICON_MOON}<span class="t">Tryb ciemny</span></button></div>'
        f'<a id="report-link" href="{home}?zglos={rel}"><span aria-hidden="true">🐞</span><span class="t">Zgłoś błąd</span></a>'
        + script
    )


OLD = re.compile(r'(?:<style>#site-bar.*?</style>)?(?:<div id="site-bar">)?<a id="home-link".*?</script>', re.S)

for f in sorted(root.rglob('*.html')):
    rel = f.relative_to(root).as_posix()
    if rel.startswith('google') or '/konkurs-biologiczny/' in rel:
        continue
    s = f.read_text(encoding='utf-8')
    s = HEAD_RE.sub('', s)
    s = re.sub(r'(<head[^>]*>)', lambda m: m.group(1) + HEAD, s, count=1)
    if rel in SKIP:
        f.write_text(s, encoding='utf-8')
        print('ok', rel, 'tylko motyw')
        continue
    m = OLD.search(s)
    if not m:
        print('brak paska', rel)
        continue
    follows = 'MutationObserver' in m.group(0)
    home = '../index.html' if '/' in rel else 'index.html'
    s = s[:m.start()] + bar(home, rel[:-5], follows) + s[m.end():]
    f.write_text(s, encoding='utf-8')
    print('ok', rel, 'lang z <html>' if follows else 'lang ze strony')
