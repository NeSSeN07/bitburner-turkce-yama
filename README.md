# Bitburner Türkçe Yama

Bitburner (Steam App ID **1812820**) için topluluk Türkçe dil yaması ve yama aracı.

> Amaç: Türk oyunculara faydası dokunmak. Bitburner açık kaynak bir oyundur; bu yama
> oyunun İngilizce metinlerini Türkçe ile değiştirir.

---

## Önce bilinmesi gerekenler (önemli)

Bitburner'ın **dil (i18n) altyapısı yoktur.** Çoğu oyunun aksine çevrilecek hazır bir
`tr.json` dil dosyası bulunmaz. Oyun, React/TypeScript ile yazılıp tek bir dosyaya
(`main.bundle.js`, ~5 MB) derlenmiş bir Electron uygulamasıdır ve tüm İngilizce metinler
bu dosyanın içine gömülüdür.

Bu yüzden "yama", bu dosyadaki İngilizce metinleri Türkçe karşılıklarıyla **güvenli şekilde
değiştirmek** demektir. Bunun birkaç sonucu var:

- **Kapsam kısmidir.** Bu ilk sürüm arayüzün büyük kısmını, yaygın mesajları ve bir dizi
  augmentation / hikaye / Corporation / Go açıklamasını çevirir. Oyundaki *tüm* metin
  (özellikle oyun içi NS API dokümanları) henüz çevrilmemiştir. Sözlük genişletilebilir.
- **Oyun güncellemesi yamayı siler.** Steam her güncellemede `main.bundle.js`'i yeniden
  indirir. Güncellemeden sonra yamayı **tekrar uygula**man gerekir (`python3 patch.py uygula`).
- **Terim politikası: Karma.** Yerleşik teknik terimler ve özel adlar İngilizce bırakılır
  (ör. `Hacking, Terminal, Faction, Augmentation, Bladeburner, Gang, Corporation, Hacknet,
  Sleeve, Stock, BitNode, Source-File, Go/IPvGO, RAM, script, server, hash` ve tüm
  fraksiyon/şirket/şehir/augmentation adları). Cümleler, etiketler ve açıklamalar Türkçeye
  çevrilir. Böylece oyuncuların alışkın olduğu terimler korunur.

---

## Gereksinimler

- Python 3 (standart kütüphane; ek paket yok)
- Linux / Windows / macOS fark etmez (yol otomatik Steam Linux kurulumuna ayarlıdır,
  farklıysa `--bundle` ile ver)

## Kullanım

```bash
# Durum: yama uygulanmış mı, yedek var mı, kaç çeviri var?
python3 patch.py durum

# Yamayı uygula (ilk çalıştırmada otomatik yedek alır)
python3 patch.py uygula

# Önce denemek için (hiçbir şeyi değiştirmeden neyin değişeceğini göster)
python3 patch.py uygula --kuru --ayrintili

# Orijinale geri dön (yedekten)
python3 patch.py geri-al
```

### Oyun dosyası başka bir yerdeyse

Varsayılan yol:
`/opt/SteamLibrary/steamapps/common/Bitburner/resources/app/dist/main.bundle.js`

Farklıysa:

```bash
python3 patch.py --bundle "/BAŞKA/YOL/main.bundle.js" uygula
```

> İpucu: Steam'de **Bitburner → Yönet → Yerel dosyalara göz at** ile klasörü bulabilirsin.
> Dosya `resources/app/dist/main.bundle.js` içindedir.

---

## Güvenlik

- Yama uygulanmadan önce orijinal dosya `main.bundle.js.tr-backup` olarak yedeklenir.
- Metinler **tırnaklarıyla birlikte** aranıp değiştirilir (`"Metin"` / `'Metin'`), böylece
  değişken/enum gibi kod tanımlayıcıları yanlışlıkla bozulmaz.
- Türkçe metinlerdeki kesme işareti / tırnak otomatik kaçışlanır (JS bozulmaz).
- Yamalı dosyanın geçerli JavaScript olduğu `node --check` ile doğrulanmıştır.
- Bir şey ters giderse: `python3 patch.py geri-al` **veya** Steam'de
  **Bitburner → Yönet → Yüklü dosyalar → Oyun dosyalarının bütünlüğünü doğrula**.

Yama "bozuk kayıt" (save) riski taşımaz: özel adlar ve kayıt içinde saklanan değerler
İngilizce bırakıldığı için mevcut oyun kayıtların etkilenmez.

---

## Sözlüğü genişletmek (katkı)

Çeviriler `sozluk/` klasöründeki JSON dosyalarındadır:

- `01-arayuz.json`   — butonlar, menüler, etiketler, ayarlar
- `02-mesajlar.json` — oyun mesajları, bildirimler, tooltip'ler, suç eylemleri
- `03-aciklamalar.json` — augmentation açıklamaları, lore/hikaye, Corporation & Go rehberleri

Her dosyanın biçimi:

```json
{
  "ceviriler": {
    "İngilizce birebir metin": "Türkçe karşılığı"
  }
}
```

**Yeni çeviri eklemek için:** Önce oyundaki İngilizce metni birebir öğren. Yardımcı araç
bundle'daki tüm doğal dil metinlerini çıkarır:

```bash
python3 tools/extract.py "/YOL/main.bundle.js" cikti_klasoru
# cikti_klasoru/kisa.json  (kısa etiketler)
# cikti_klasoru/orta.json  (cümleler/mesajlar)
# cikti_klasoru/uzun.json  (açıklamalar/lore)
```

Çıkan metni (tırnak içindeki haliyle, birebir) bir sözlük dosyasına anahtar olarak ekle,
Türkçesini değer yap. Ardından:

```bash
python3 patch.py uygula --kuru --ayrintili   # eşleşiyor mu kontrol et
python3 patch.py uygula                       # uygula
```

`--ayrintili`, eşleşmeyen (yani bundle'da birebir bulunamayan) girdileri listeler —
bir metni yanlış kopyaladıysan burada görürsün.

---

## Sürüm

- Hazırlandığı Bitburner sürümü: **3.0.1** (package.json), buildid 23272653
- İlk sürüm çeviri sayısı: **384** girdi, ~517 metin değişikliği

Başka bir Bitburner sürümünde bazı metinler değişmiş olabilir; eşleşmeyenler atlanır,
oyun yine çalışır. Sözlüğü yeni sürüme göre güncellemen yeterli.
