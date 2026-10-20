import json,re,sys
src=sys.argv[1] if len(sys.argv)>1 else 'design/v10.html'
s=open(src).read(); P=json.load(open('tools/en-map.json'))
miss=[d for d,e in P if d not in s]
for d,e in P: s=s.replace(d,e)
b=s[s.index('<body'):]
body,js=b[:b.index('<script>')],b[b.index('<script>'):]
OK=['Carøe','Skovsbøl','Dæk','Rådgivende','Djurslands','Gulvservice','Murerforretning','Byg &amp; Montage','Lagersalg','Begravelsesforretning','Gitte','Varme Pumpe','13-årige Mason Bjerring sluttede blandt Sveriges bedste juniorer i sin første formelsæson','Küdahl','Midtjysk Karting Bane','Gelleråsen','Jysk-Fynsk','Ungdomscup']
DW=r'\b(og|til|på|med|er|jeg|der|det|af|ikke|løb|fra|en|et|som|kører|alle|vores|hele|siden|banen|bil|kr)\b'
texts=re.findall(r'>([^<>]+)<',body)+re.findall(r'(?:alt|aria-label|title)="([^"]+)"',body)+re.findall(r"'([^']*)'",js)
bad=[]
for t in texts:
    u=t
    for o in OK: u=u.replace(o,'')
    if re.search(r'[æøåÆØÅ]',u) or re.search(DW,u,re.I):
        if t.strip() and t not in bad: bad.append(t.strip())
print('MISSING KEYS:',len(miss)); [print('  ',m[:100]) for m in miss]
print('DANISH LEFT:',len(bad)); [print('  ',x[:160]) for x in bad]
print('EMDASH:', '—' in s)
