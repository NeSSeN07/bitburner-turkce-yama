#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bitburner Turkce Yama Araci
===========================

Oyunun derlenmis `main.bundle.js` dosyasindaki Ingilizce metinleri, sozlukteki
Turkce karsiliklariyla GUVENLI sekilde degistirir. Oyunun i18n (dil) altyapisi
olmadigi icin tek uygulanabilir yol budur.

Guvenlik ilkeleri:
  * Varsayilan olarak metinler TIRNAKLARIYLA birlikte aranir ("Metin" / 'Metin').
    Boylece kod tanimlayicilari (degisken/enum adlari) yanlislikla bozulmaz.
  * Her uygulamadan once orijinal dosyanin yedegi alinir (.tr-backup).
  * "restore" ile her zaman orijinale donulebilir.
  * Bir ceviri hic eslesmezse uyari verilir (guncellemede metin degismis olabilir).
  * Bir Turkce karsilik kaynakta zaten varsa (cift uygulama) atlanir.

Kullanim:
    python3 patch.py durum                      # kurulum/yama durumu
    python3 patch.py uygula                      # yamayi uygula (yedek alir)
    python3 patch.py uygula --kuru               # deneme: neyin degisecegini goster, dosyaya dokunma
    python3 patch.py geri-al                     # yedekten orijinale don
    python3 patch.py --bundle /yol/main.bundle.js uygula   # yolu elle ver

Sozlukler `sozluk/` klasorundeki .json dosyalarindan okunur.
Her dosya:  { "ceviriler": { "English": "Turkce", ... } }
Opsiyonel bir girdi su formda da olabilir (ham/regex gelismis kullanim):
    "English": { "tr": "Turkce", "raw": true }   # tirnaksiz birebir degistir
"""

import argparse
import glob
import json
import os
import shutil
import sys

VARSAYILAN_BUNDLE = (
    "/opt/SteamLibrary/steamapps/common/Bitburner/"
    "resources/app/dist/main.bundle.js"
)
PROJE_DIZINI = os.path.dirname(os.path.abspath(__file__))
SOZLUK_DIZINI = os.path.join(PROJE_DIZINI, "sozluk")
YEDEK_SONEKI = ".tr-backup"
IMZA = "/*__BITBURNER_TR__*/"  # yamanin uygulandigini belirten isaret


def renk(s, kod):
    if sys.stdout.isatty():
        return f"\033[{kod}m{s}\033[0m"
    return s


def yesil(s):  return renk(s, "32")
def sari(s):   return renk(s, "33")
def kirmizi(s):return renk(s, "31")
def mavi(s):   return renk(s, "36")


def sozlukleri_yukle():
    """sozluk/*.json dosyalarini okuyup tek bir ceviri listesi dondur."""
    ceviriler = []  # (ingilizce, turkce, raw, kaynak_dosya)
    dosyalar = sorted(glob.glob(os.path.join(SOZLUK_DIZINI, "*.json")))
    if not dosyalar:
        print(kirmizi(f"Uyari: {SOZLUK_DIZINI} icinde sozluk bulunamadi."))
    toplam = 0
    for yol in dosyalar:
        with open(yol, "r", encoding="utf-8") as f:
            veri = json.load(f)
        girdiler = veri.get("ceviriler", veri)  # "ceviriler" anahtari yoksa dogrudan harita
        ad = os.path.basename(yol)
        for en, tr in girdiler.items():
            if isinstance(tr, dict):
                raw = bool(tr.get("raw", False))
                hedef = tr.get("tr", "")
            else:
                raw, hedef = False, tr
            if not hedef:
                continue  # henuz cevrilmemis girdi (bos) -> atla
            ceviriler.append((en, hedef, raw, ad))
            toplam += 1
    # uzun metinleri once uygula (kisa bir metin uzun bir metnin parcasi olabilir)
    ceviriler.sort(key=lambda t: len(t[0]), reverse=True)
    return ceviriler


def bundle_oku(yol):
    with open(yol, "r", encoding="utf-8", errors="surrogatepass") as f:
        return f.read()


def bundle_yaz(yol, icerik):
    with open(yol, "w", encoding="utf-8", errors="surrogatepass") as f:
        f.write(icerik)


def yamali_mi(icerik):
    return icerik.startswith(IMZA)


def durum(args):
    yol = args.bundle
    print(mavi("== Bitburner Turkce Yama - Durum =="))
    print(f"Bundle yolu : {yol}")
    if not os.path.exists(yol):
        print(kirmizi("  -> Dosya bulunamadi. Steam kurulumunu/yolu kontrol et."))
        return 1
    boyut = os.path.getsize(yol) / (1024 * 1024)
    print(f"Bundle boyutu: {boyut:.1f} MB")
    icerik = bundle_oku(yol)
    print("Yama durumu : " + (yesil("UYGULANMIS") if yamali_mi(icerik) else sari("uygulanmamis")))
    yedek = yol + YEDEK_SONEKI
    print("Yedek       : " + (yesil(f"var ({yedek})") if os.path.exists(yedek) else sari("yok")))
    ceviriler = sozlukleri_yukle()
    print(f"Sozlukteki ceviri sayisi: {len(ceviriler)}")
    return 0


def uygula(args):
    yol = args.bundle
    if not os.path.exists(yol):
        print(kirmizi(f"Hata: bundle bulunamadi: {yol}"))
        return 1

    ceviriler = sozlukleri_yukle()
    if not ceviriler:
        print(kirmizi("Sozluk bos; yapacak bir sey yok."))
        return 1

    icerik = bundle_oku(yol)

    # Yama daha once uygulanmissa once yedekten temiz baslangic yap
    yedek = yol + YEDEK_SONEKI
    if yamali_mi(icerik):
        if os.path.exists(yedek):
            print(sari("Yama zaten uygulanmis; once yedekten temiz kopyaya donuluyor."))
            icerik = bundle_oku(yedek)
        else:
            print(kirmizi("Yama uygulanmis ama yedek yok! 'geri-al' yapilamaz. "
                          "Steam'de 'Dosya butunlugunu dogrula' calistirip tekrar dene."))
            return 1
    else:
        # ilk uygulama: yedek al
        if not args.kuru:
            if not os.path.exists(yedek):
                shutil.copy2(yol, yedek)
                print(yesil(f"Yedek alindi: {yedek}"))

    uygulanan = 0
    atlanan_eslesme_yok = []
    toplam_degisiklik = 0
    for en, tr, raw, kaynak in ceviriler:
        if raw:
            aranan, yeni = en, tr
        else:
            # cift ve tek tirnakli iki varyanti da dene
            aranan = None
            yeni = None
        if raw:
            adet = icerik.count(aranan)
            if adet:
                icerik = icerik.replace(aranan, yeni)
                uygulanan += 1
                toplam_degisiklik += adet
            else:
                atlanan_eslesme_yok.append((en, kaynak))
            continue

        # tirnakli guvenli degistirme
        bu_girdi_degisti = False
        for q in ('"', "'"):
            kaynak_desen = f"{q}{en}{q}"
            # Turkce metinde gecen tirnak/kesme isaretini ve ters egik cizgiyi,
            # icinde bulundugu tirnak turune gore KACISLA; aksi halde JS bozulur.
            tr_guvenli = tr.replace("\\", "\\\\").replace(q, "\\" + q)
            hedef_desen = f"{q}{tr_guvenli}{q}"
            adet = icerik.count(kaynak_desen)
            if adet:
                icerik = icerik.replace(kaynak_desen, hedef_desen)
                toplam_degisiklik += adet
                bu_girdi_degisti = True
        if bu_girdi_degisti:
            uygulanan += 1
        else:
            atlanan_eslesme_yok.append((en, kaynak))

    print()
    print(f"Uygulanan ceviri   : {yesil(str(uygulanan))}/{len(ceviriler)}")
    print(f"Toplam metin degisikligi: {toplam_degisiklik}")
    if atlanan_eslesme_yok:
        print(sari(f"Eslesmeyen (muhtemelen guncellemede degismis) : {len(atlanan_eslesme_yok)}"))
        if args.ayrintili:
            for en, kaynak in atlanan_eslesme_yok[:50]:
                kisalt = (en[:60] + "...") if len(en) > 60 else en
                print(sari(f"   [{kaynak}] {kisalt!r}"))

    if args.kuru:
        print(mavi("\n[KURU CALISMA] Dosya degistirilmedi."))
        return 0

    # imza ekle
    if not icerik.startswith(IMZA):
        icerik = IMZA + icerik
    bundle_yaz(yol, icerik)
    print(yesil("\nYama uygulandi. Oyunu baslatip kontrol edebilirsin."))
    print("Geri almak icin:  python3 patch.py geri-al")
    return 0


def geri_al(args):
    yol = args.bundle
    yedek = yol + YEDEK_SONEKI
    if not os.path.exists(yedek):
        print(kirmizi(f"Yedek bulunamadi: {yedek}"))
        print("Steam -> Bitburner -> Ozellikler -> Yuklu Dosyalar -> "
              "'Oyun dosyalarinin butunlugunu dogrula' ile orijinali geri getirebilirsin.")
        return 1
    shutil.copy2(yedek, yol)
    print(yesil(f"Orijinal geri yuklendi ({yedek} -> {yol})."))
    return 0


def main():
    p = argparse.ArgumentParser(description="Bitburner Turkce Yama Araci")
    p.add_argument("--bundle", default=VARSAYILAN_BUNDLE,
                   help="main.bundle.js yolu (varsayilan: Steam kurulumu)")
    alt = p.add_subparsers(dest="komut", required=True)

    pd = alt.add_parser("durum", help="Kurulum ve yama durumunu goster")
    pd.set_defaults(fn=durum)

    pu = alt.add_parser("uygula", help="Yamayi uygula")
    pu.add_argument("--kuru", action="store_true", help="Deneme; dosyaya yazma")
    pu.add_argument("--ayrintili", action="store_true", help="Eslesmeyen metinleri listele")
    pu.set_defaults(fn=uygula)

    pg = alt.add_parser("geri-al", help="Yedekten orijinale don")
    pg.set_defaults(fn=geri_al)

    args = p.parse_args()
    sys.exit(args.fn(args))


if __name__ == "__main__":
    main()
