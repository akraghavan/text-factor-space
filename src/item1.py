import re, html as ihtml
TAG=re.compile(r'<[^>]+>'); WS=re.compile(r'\s+')
STYLE=re.compile(r'(?is)<(script|style|head)[^>]*>.*?</\1>')
HIDDEN=re.compile(r'(?is)<ix:header>.*?</ix:header>')
def to_text(raw:str)->str:
    raw=HIDDEN.sub(' ',raw); raw=STYLE.sub(' ',raw)
    raw=re.sub(r'(?i)<br\s*/?>|</(p|div|tr|li|h\d)>','\n',raw)
    t=TAG.sub(' ',raw); t=ihtml.unescape(t).replace('\xa0',' ')
    return WS.sub(' ',t)
L=lambda w: r'\s*'.join(w)          # tolerate s p a c e d letters
START=re.compile(r'(?i)item\s*1\s*[\.\:\-–—]?\s*(?:and\s*2\s*[\.\:\-–—]?\s*)?'+L('business'))
END=re.compile(r'(?i)item\s*1\s*a\s*[\.\:\-–—]?\s*'+L('risk')+r'|item\s*1\s*b\s*[\.\:\-–—]?\s*'+L('unresolved')+r'|item\s*2\s*[\.\:\-–—]?\s*'+L('properties')+r'|item\s*1\s*c\s*[\.\:\-–—]?\s*'+L('cybersecurity'))
def extract_item1(text:str):
    starts=[m.start() for m in START.finditer(text)]
    ends=[m.start() for m in END.finditer(text)]
    best=None
    for a in starts:
        b=next((e for e in ends if e>a+200),None)
        if b is None: continue
        if any(a<s2<b for s2 in starts): continue   # a is a TOC entry: another 'Item 1' start precedes the end
        if best is None or (b-a)>(best[1]-best[0]): best=(a,b)
    if best is None: return None
    return text[best[0]:best[1]]
