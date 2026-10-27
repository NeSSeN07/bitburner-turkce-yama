#!/usr/bin/env python3
"""
Bitburner bundle string extractor (gelistirme araci).

main.bundle.js icindeki cift tirnakli ("...") ve tek tirnakli ('...')
string literalleri cikarir, dogal dil gibi gorunenleri filtreler ve
kategorilere ayirir. Amac: cevrilecek GERCEK metinleri birebir yakalamak.

Kullanim:
    python3 extract.py /yol/main.bundle.js  cikti_klasoru
"""
import sys, os, re, json, html

def extract_string_literals(src: str):
    """JS kaynak metninden "..." ve '...' literallerini cikar (kacis dizilerini korur)."""
    out = []
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if c == '"' or c == "'":
            q = c
            j = i + 1
            buf = []
            while j < n:
                cj = src[j]
                if cj == '\\':
                    buf.append(src[j:j+2])
                    j += 2
                    continue
                if cj == q:
                    break
                if cj == '\n':
                    # tirnak kapanmadan satir bitti -> muhtemelen literal degil
                    buf = None
                    break
                buf.append(cj)
                j += 1
            if buf is not None and j < n:
                out.append(''.join(buf))
                i = j + 1
                continue
            i += 1
        else:
            i += 1
    return out


CODE_SIGNS = ('=>', '});', '){', '](', '||', '&&', '::', '0x', '/>', '<svg',
              'function', 'return ', 'var ', 'const ', 'let ', 'typeof',
              'undefined', 'null)', '.createElement', 'className')


def looks_like_prose(s: str) -> bool:
    """Dogal dil metni mi? (kod/webpack parcasi / url / yol / kimlik degil)"""
    if len(s) < 3:
        return False
    txt = s.replace('\\n', ' ').replace('\\t', ' ').replace("\\'", "'").replace('\\"', '"')
    low = txt
    # acik kod isaretleri
    for sign in CODE_SIGNS:
        if sign in low:
            return False
    # webpack modul listesi gibi: cok sayida "=n(" ya da ":()=>"
    if low.count('(') + low.count(')') >= 4:
        return False
    if re.search(r'=\w+\(\d', low):          # =n(296540) kaliplari
        return False
    if re.fullmatch(r'[\w./\-]+', txt):       # tek token: url/yol/kimlik
        return False
    if txt.startswith('http') or txt.startswith('./') or txt.startswith('/'):
        return False
    if re.fullmatch(r'[0-9.,:%+\-/*() ]+', txt):
        return False
    if not re.search(r'[A-Za-z]', txt):
        return False
    # harf+bosluk orani: dogal dilde yuksektir, minified kodda dusuk
    harf_bosluk = sum(1 for c in txt if c.isalpha() or c == ' ')
    if harf_bosluk / len(txt) < 0.6:
        return False
    # cok fazla ozel karakter / noktalama bitisigi
    if re.search(r'[{}<>$`\\|]', txt):
        return False
    if re.search(r'[A-Za-z]\.[A-Za-z]\.[A-Za-z]', txt):  # a.b.c zincirleri
        return False
    return True


def categorize(s: str) -> str:
    txt = s.replace('\\n', ' ')
    words = len(txt.split())
    if words >= 12:
        return 'uzun'      # paragraf/aciklama (fraksiyon, augmentation, hikaye)
    if words >= 4:
        return 'orta'      # cumle/tooltip/mesaj
    return 'kisa'          # menu/buton/etiket


def main():
    bundle = sys.argv[1]
    outdir = sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    with open(bundle, 'r', encoding='utf-8', errors='replace') as f:
        src = f.read()

    lits = extract_string_literals(src)
    # tekille + say
    counts = {}
    for s in lits:
        counts[s] = counts.get(s, 0) + 1

    prose = {s: c for s, c in counts.items() if looks_like_prose(s)}

    buckets = {'kisa': [], 'orta': [], 'uzun': []}
    for s, c in prose.items():
        buckets[categorize(s)].append((s, c))

    for name, items in buckets.items():
        # uzun metinleri once, kisa menuleri alfabetik
        items.sort(key=lambda t: (-len(t[0]), t[0]))
        path = os.path.join(outdir, f'{name}.json')
        # JSON: {"ingilizce": tekrar_sayisi}
        obj = {s: c for s, c in items}
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent=1)
        print(f'{name}: {len(items)} benzersiz metin -> {path}')

    print(f'Toplam benzersiz dogal-dil metni: {len(prose)}')


if __name__ == '__main__':
    main()
