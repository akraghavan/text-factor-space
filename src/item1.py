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

# v2 fallback (27 Sep 2026): line-aware. v1 flattens the text, so it cannot tell a heading from a cross-reference
# ("see Item 1. Business—Our Customers") and misses "Items 1 and 2", "Item 1 | Business", "Description of Business",
# "I tem 1" and zero-width characters. v2 keeps block-level line breaks and accepts headings only at the start of a line.
# Used only where v1 yields < 300 words, so the v1 extracts (and everything built on them) are unchanged.
ZW=re.compile('[​‌‍⁠﻿]')
BLOCK=re.compile(r'(?i)<br\s*/?>|</?(?:p|div|tr|li|h\d|table|center)\b[^>]*>')
ITEM=r'i\s*t\s*e\s*m\s*s?'; SEP=r'[\s\.\:\-–—|,]*'; PART=r'(?:part\s*i\b[\s\.\:\-–—,]*)?'
START2=re.compile(r'(?i)^'+PART+ITEM+r'\s*1(?![0-9a-z])'+SEP+r'(?:(?:and|&)?\s*1\s*a'+SEP+r')?(?:(?:and|&)\s*2'+SEP+r')?'
                  r'(?:(?:description\s*of|our|the)\s*(?:the\s*)?)?'+L('business'))
END2=re.compile(r'(?i)^'+PART+ITEM+r'\s*(?:1\s*[abc]|[234])(?![0-9a-z])'+SEP+r'(?:[a-z]|$)')
BARE1=re.compile(r'(?i)^'+PART+ITEM+r'\s*1'+SEP+r'(?:(?:and|&)\s*2'+SEP+r')?(?:description\s*of\s*)?$')   # "Item 1." / "Items 1 and 2." / "Item 1. Description of" alone: title on the next line
def to_lines(raw:str)->list:
    raw=HIDDEN.sub(' ',raw); raw=STYLE.sub(' ',raw); raw=BLOCK.sub('\n',raw)
    t=ZW.sub('',ihtml.unescape(TAG.sub(' ',raw))).replace('\xa0',' ')
    lines=[re.sub(r'[^\S\n]+',' ',l).strip() for l in t.split('\n')]
    lines=[l for l in lines if l]
    return [l+' '+lines[i+1] if BARE1.match(l) and i+1<len(lines) else l for i,l in enumerate(lines)]
def extract_item1_v2(raw_html:str):
    """Longest start-heading -> next-item-heading span, headings matched at line starts only. Returns text or None."""
    lines=to_lines(raw_html)
    starts=[i for i,l in enumerate(lines) if START2.match(l)]
    ends=[i for i,l in enumerate(lines) if END2.match(l)]
    best=None; bw=0
    for a in starts:
        b=next((e for e in ends if e>a),None)
        if b is None: continue
        w=sum(len(l.split()) for l in lines[a:b])
        if w>bw: best,bw=(a,b),w
    return None if best is None else ' '.join(lines[best[0]:best[1]])
