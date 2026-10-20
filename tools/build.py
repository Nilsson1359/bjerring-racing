#!/usr/bin/env python3
"""Bygger forsiden (index.html) og den engelske udgave (en/index.html) ud fra design/v10.html.

Kør fra repo-roden:  python3 tools/build.py
- Alle asset-stier gøres absolutte (/assets/...), så begge sprog deler filer.
- Billeder skiftes til WebP med srcset/width/height (se tools/img-manifest.json).
- Skrifttyper er selv-hostede (tools/fonts.css -> /assets/fonts/).
- en/index.html laves ved at anvende tools/en-map.json (ordnede [dansk, engelsk]-par) på body.
"""
import json, re, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

src = open('design/v10.html', encoding='utf-8').read()
manifest = json.load(open('tools/img-manifest.json'))
fonts_css = open('tools/fonts.css').read().replace("url(assets/fonts/", "url(/assets/fonts/")
fonts_css = re.sub(r'\s*\n\s*', '', fonts_css)
# Overskrifts-skrifter vises først når de er hentet (forudindlæst, små) så layoutet ikke hopper;
# brødtekst bruger en Arial-fallback med Inter-mål, så skiftet ikke flytter noget.
fonts_css = fonts_css.replace("font-family: 'Saira';font-style: italic;", "font-family: 'Saira';font-style: italic;font-display: block;")
fonts_css = fonts_css.replace("font-family: 'Kaushan Script';", "font-family: 'Kaushan Script';font-display: block;")
fonts_css = re.sub(r"(font-family: '(?:Saira|Kaushan Script)';font-style: italic;font-display: block;[^}]*?)font-display: swap;", r"\1", fonts_css)
fonts_css = re.sub(r"(font-family: 'Kaushan Script';font-display: block;[^}]*?)font-display: swap;", r"\1", fonts_css)
fonts_css += "@font-face{font-family:'Inter Fallback';src:local('Arial');size-adjust:107.1%;ascent-override:90.4%;descent-override:22.5%;line-gap-override:0%}"


# ---------- split ----------
style = src[src.index('<style>') + 7: src.index('</style>')]
body = src[src.index('<body'): src.index('</html>')]

# ---------- body: paths ----------
body = body.replace('../assets/', '/assets/').replace('"assets/mason-', '"/assets/mason-').replace("'assets/mason-", "'/assets/mason-")
# variant-pille ud
body = re.sub(r'\n?<a class="vpill"[^>]*>.*?</a>\n?', '\n', body)

# ---------- body: images -> webp ----------
def webp_set(name):
    m = manifest[name]
    base = name.rsplit('.', 1)[0]
    if name.startswith('sp26'):
        return f'/assets/{base}.webp', None, m['w'], m['h']
    sizes = m['sizes']
    ratio = m['h'] / m['w']
    srcset = ', '.join(f'/assets/{base}-{w}.webp {w}w' for w in sizes)
    return f'/assets/{base}-{sizes[0]}.webp', srcset, sizes[-1], round(sizes[-1] * ratio)

def img_sub(mo):
    tag = mo.group(0)
    s = re.search(r'src="/assets/([\w\-]+\.(?:jpg|png))"', tag)
    if not s:
        return tag
    name = s.group(1)
    url, srcset, w, h = webp_set(name)
    new = tag.replace(s.group(0), f'src="{url}"')
    attrs = f' width="{w}" height="{h}"'
    if srcset and len(manifest[name]['sizes']) > 1:
        attrs += f' srcset="{srcset}" sizes="(max-width:760px) 100vw, 50vw"'
    if 'loading=' not in new:
        attrs += ' loading="lazy"'
    if 'decoding=' not in new:
        attrs += ' decoding="async"'
    return new[:-1] + attrs + '>'

body = re.sub(r'<img\b[^>]*>', img_sub, body)

# galleri-links (åbner stort billede) -> største webp
def href_sub(mo):
    name = mo.group(1)
    m = manifest.get(name)
    if not m or not m['sizes']:
        return mo.group(0)
    return f'href="/assets/{name.rsplit(".",1)[0]}-{m["sizes"][-1]}.webp"'
body = re.sub(r'href="/assets/([\w\-]+\.jpg)"', href_sub, body)

# video-plakater -> webp, og hent kun video ved klik
def poster_sub(mo):
    name = mo.group(1)
    m = manifest.get(name)
    if not m:
        return mo.group(0)
    return f'poster="/assets/{name.rsplit(".",1)[0]}-{m["sizes"][0]}.webp"'
body = re.sub(r'poster="/assets/([\w\-]+\.jpg)"', poster_sub, body)
body = body.replace('controls preload="metadata"', 'controls preload="none"')

# sprog-knap i menuen
body = body.replace('      <a href="#kontakt" class="btn btn-y">Bliv sponsor</a>\n    </div>',
    '      <a href="/en/" class="lang" hreflang="en" lang="en" title="Read in English" onclick="try{localStorage.setItem(\'br-lang\',\'en\')}catch(e){}">EN</a>\n'
    '      <a href="#kontakt" class="btn btn-y">Bliv sponsor</a>\n    </div>', 1)
assert 'class="lang"' in body, 'sprog-knap ikke indsat'

# besøgstæller (cookiefri) fra den gamle forside
body = body.replace('</body>', '''<script>
/* Cookiefri besøgstælling på egen server. Gemmer ingen cookies eller IP-adresser. */
(function(){try{navigator.sendBeacon('https://stats.appsendmates.site/hit',JSON.stringify({p:location.pathname,r:document.referrer}))}catch(e){}})();
</script>
</body>''')

# tilgængelighed: logo-link får sit navn fra den synlige tekst; lysere fodnote
body = body.replace(' aria-label="Bjerring Racing, til toppen"', '')
style = style.replace('.sector h4{', 'h3.h4{font-style:normal;font-stretch:100%;line-height:1.15}\n.sector h4{').replace('.sector h4{', '.sector h3.h4{').replace('.btnw h4{', '.btnw h3.h4{')
style += '\n.foot-note{color:#8b8d93}\n'
# heltevideo hentes først når siden er færdig (sparer båndbredde i første visning)
body = body.replace("else{hv.src='/assets/mason-onboard.mp4';var p=hv.play();if(p&&p.catch)p.catch(function(){});}",
  "else{var go=function(){hv.src='/assets/mason-onboard.mp4';var p=hv.play();if(p&&p.catch)p.catch(function(){});};if(document.readyState==='complete')go();else window.addEventListener('load',function(){setTimeout(go,150)});}")
assert "window.addEventListener('load',function(){setTimeout(go" in body, 'video-udsættelse ikke indsat'

style += '\n.links a.lang{font-family:var(--hud);font-weight:700;letter-spacing:.08em;font-size:.8rem;border:1px solid var(--line2);padding:4px 8px}\n'
style = style.replace('.vpill', '.vpill-unused')
style = style.replace("font-family:'Inter',system-ui,sans-serif", "font-family:'Inter','Inter Fallback',system-ui,sans-serif")

# ---------- head ----------
CAL = [
    ('Gelleråsen Arena', '2026-05-30', '2026-05-31', 'SE', 'Aquila Formula 1000'),
    ('Mittsverigebanan', '2026-06-13', '2026-06-14', 'SE', 'Aquila Formula 1000'),
    ('Midtjysk Karting Bane', '2026-06-19', '2026-06-21', 'DK', 'Gokart DM'),
    ('Sturup Raceway', '2026-06-27', '2026-06-28', 'SE', 'Aquila Formula 1000'),
    ('Ring Knutstorp', '2026-07-04', '2026-07-05', 'SE', 'Aquila Formula 1000'),
    ('Kinnekulle Ring', '2026-07-25', '2026-07-26', 'SE', 'Aquila Formula 1000'),
    ('Rudskogen', '2026-08-08', '2026-08-09', 'NO', 'Aquila Formula 1000'),
    ('Ring Djursland', '2026-09-19', '2026-09-20', 'DK', 'Aquila Formula 1000'),
]

def head(lang):
    da = lang == 'da'
    url = 'https://bjerringracing.dk/' + ('' if da else 'en/')
    title = ('Bjerring Racing · Mason Bjerring #10 · Fra Gokart til Racerbil' if da
             else 'Bjerring Racing · Mason Bjerring #10 · From Go-Kart to Race Car')
    desc = ('Mason Max Carøe Bjerring, 14 år, kører Aquila Formula 1000 under KEDA Motorsport. P3 i svensk Junior-RM i debutsæsonen. Se løb, resultater og videoer, og bliv sponsor.' if da
            else 'Mason Max Carøe Bjerring, 14, races the Aquila Formula 1000 for KEDA Motorsport. P3 in the Swedish Junior Championship in his debut season. Races, results, videos and sponsorship.')
    person = {
        "@context": "https://schema.org", "@type": "Person",
        "name": "Mason Max Carøe Bjerring", "alternateName": "Mason Bjerring",
        "jobTitle": "Racerkører" if da else "Racing driver", "nationality": "Danish",
        "url": url, "image": "https://bjerringracing.dk/assets/og-image.jpg",
        "description": ("Dansk racerkører (14 år), startnummer 10. Kører Aquila Formula 1000 under KEDA Motorsport." if da
                        else "Danish racing driver (14), car number 10. Races the Aquila Formula 1000 for KEDA Motorsport."),
        "memberOf": {"@type": "SportsTeam", "name": "KEDA Motorsport"},
        "sameAs": ["https://www.instagram.com/bjerring_racing", "https://www.facebook.com/bjerringracing", "https://www.tiktok.com/@bjerring_racing"],
    }
    org = {
        "@context": "https://schema.org", "@type": ["Organization", "SportsTeam"],
        "name": "Bjerring Racing", "alternateName": ["Mason Bjerring Racing"],
        "url": "https://bjerringracing.dk/", "logo": "https://bjerringracing.dk/assets/br-mark.svg",
        "image": "https://bjerringracing.dk/assets/og-image.jpg", "sport": "Motorsport",
        "description": ("Bjerring Racing. Mason Bjerring, dansk racerkører nummer 10, kører Aquila Formula 1000 under KEDA Motorsport. Søger sponsorer." if da
                        else "Bjerring Racing. Mason Bjerring, Danish racing driver number 10, races the Aquila Formula 1000 for KEDA Motorsport. Looking for sponsors."),
        "athlete": {"@type": "Person", "name": "Mason Max Carøe Bjerring"},
        "sameAs": person["sameAs"],
    }
    events = {
        "@context": "https://schema.org", "@type": "ItemList",
        "name": "Bjerring Racing race-kalender 2026" if da else "Bjerring Racing race calendar 2026",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "item": {
                "@type": "SportsEvent", "name": f"{cls} · {venue}", "startDate": s, "endDate": e, "sport": "Motorsport",
                "location": {"@type": "Place", "name": venue, "address": {"@type": "PostalAddress", "addressCountry": c}},
                "performer": {"@type": "Person", "name": "Mason Bjerring"},
                "organizer": {"@type": "Organization", "name": "KEDA Motorsport"},
                "eventStatus": "https://schema.org/EventScheduled"}}
            for i, (venue, s, e, c, cls) in enumerate(CAL)],
    }
    site = {"@context": "https://schema.org", "@type": "WebSite", "name": "Bjerring Racing", "url": url, "inLanguage": "da-DK" if da else "en"}
    ld = '\n'.join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in (person, org, events, site))

    if da:
        langscript = '''<script>
/* Sprogvalg: besøgende uden for Danmark sendes til den engelske udgave (/en/).
   IP-landeopslag uden cookies; valget huskes i localStorage, og manuelt skift vinder altid. */
(function(){try{
  if(location.search.indexOf('lang=da')>-1){localStorage.setItem('br-lang','da');return;}
  var pref=localStorage.getItem('br-lang');
  if(pref==='da')return;
  if(pref==='en'){location.replace('/en/');return;}
  if(/bot|crawl|spider|lighthouse/i.test(navigator.userAgent))return;
  fetch('https://api.country.is/').then(function(r){return r.json()}).then(function(d){
    if(d&&d.country&&d.country!=='DK'){localStorage.setItem('br-lang','en');location.replace('/en/');}
    else if(d&&d.country){localStorage.setItem('br-lang','da');}
  }).catch(function(){});
}catch(e){}})();
</script>'''
    else:
        langscript = '''<script>
/* Language choice: remember that the visitor is on the English version. */
(function(){try{if(location.search.indexOf('lang=en')>-1||!localStorage.getItem('br-lang'))localStorage.setItem('br-lang','en');}catch(e){}})();
</script>'''

    return f'''<!DOCTYPE html>
<html lang="{'da' if da else 'en'}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="robots" content="index, follow, max-image-preview:large">
<meta name="author" content="Bjerring Racing">
<meta name="theme-color" content="#0a0a0b">
<link rel="canonical" href="{url}">
<link rel="alternate" hreflang="da" href="https://bjerringracing.dk/">
<link rel="alternate" hreflang="en" href="https://bjerringracing.dk/en/">
<link rel="alternate" hreflang="x-default" href="https://bjerringracing.dk/">
{langscript}
<link rel="preload" href="/assets/fonts/Saira-fa4952.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/Inter-1ab1ad.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/SairaCondensed-1c5f1e.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/KaushanScript-6f0301.woff2" as="font" type="font/woff2" crossorigin>
<meta property="og:type" content="website">
<meta property="og:site_name" content="Bjerring Racing">
<meta property="og:locale" content="{'da_DK' if da else 'en_GB'}">
<meta property="og:locale:alternate" content="{'en_GB' if da else 'da_DK'}">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="https://bjerringracing.dk/assets/og-image.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Mason Bjerring #10, Bjerring Racing">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="https://bjerringracing.dk/assets/og-image.jpg">
<link rel="icon" type="image/png" sizes="32x32" href="/assets/favicon-32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/assets/favicon-16.png">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
{ld}
<style>
{fonts_css}
{style}
</style>
<noscript><style>.rv{{opacity:1!important;transform:none!important}}</style></noscript>
</head>
'''

def fix_headings(b):
    return b.replace('<h4>', '<h3 class="h4">').replace('</h4>', '</h3>')

def no_emdash(s, where):
    assert '—' not in s, f'em dash i {where}'

da_html = head('da') + fix_headings(body) + '</html>\n'
no_emdash(da_html, 'index.html')
open('index.html', 'w', encoding='utf-8').write(da_html)
print('index.html', len(da_html))

# ---------- engelsk ----------
if os.path.exists('tools/en-map.json'):
    pairs = json.load(open('tools/en-map.json', encoding='utf-8'))
    en_body = body
    for da_s, en_s in pairs:
        en_body = en_body.replace(da_s, en_s)
    # sprog-knap: på engelsk peger den tilbage til dansk
    en_body = re.sub(r'<a href="/en/" class="lang"[^>]*>EN</a>',
        '<a href="/?lang=da" class="lang" hreflang="da" lang="da" title="Læs på dansk" onclick="try{localStorage.setItem(\'br-lang\',\'da\')}catch(e){}">DA</a>', en_body)
    en_html = head('en') + fix_headings(en_body) + '</html>\n'
    no_emdash(en_html, 'en/index.html')
    os.makedirs('en', exist_ok=True)
    open('en/index.html', 'w', encoding='utf-8').write(en_html)
    print('en/index.html', len(en_html))
else:
    print('tools/en-map.json mangler endnu, en/index.html ikke bygget', file=sys.stderr)
