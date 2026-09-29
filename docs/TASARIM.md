# Tasarım: dizin sayfası

## Hedef

Videodan ya da profilden gelen biri sayfayı açtığında üç şeyi hemen görür: bu hesap ne yapıyor
(ajan altyapısı, MCP sunucuları, geliştirici araçları), kaç şey var (28 depo, test sayıları) ve aradığını
nasıl bulur (arama + süzgeç). Görsel dil günlük videolarla aynı: FRK-OS. Sayfa üreticiden çıkıyor;
tasarım `sablon.html` içinde, davranış `uret.py` içinde, elle `index.html` düzenlenmez.

## Önce / sonra

| | Önce | Sonra |
|---|---|---|
| Zemin, yazı, vurgu | `#0b0b0f`, gri-mavi metin, soluk altın `#c9a961`, yeşil/mavi/pembe çipler | `#0e0d0b` siyah, `#f1ece2` krem, `#ffc21a` sarı; çipler sarı / camgöbeği `#19d3e6` / mercan |
| Başlık | Cascadia Code 40 px | League Gothic, büyük harf, sarı çubuk imza |
| Etiketler | sistem monospace | JetBrains Mono (çipler, düğmeler, sayaç, bağlantı satırı) |
| Dil | yalnız İngilizce | Türkçe + İngilizce, ilk açılışta `navigator.language`, seçim `localStorage`'da |
| Hareket | yok | açılışta iris, kartlarda itme girişi, süzgeçte zoom + flaş (yalnız hareket tercihi varsa) |
| Sayaç | yalnız ekran okuyucuya | görünür `6 / 28` sayacı |
| Oyun kartları | "Live" | kendi sayfası olan oyunda "Play / Oyna" |
| Erişilebilirlik | Lighthouse 96 | Lighthouse 100 |
| Boyut | 89 KiB | 148 KiB (45 KiB yerel yazı tipi) |

Görseller: `D:\Claude Projeleri\proje-yenileme\kanit\Furkiozknn.github.io\once` ve `\sonra` (mobil 390x844,
masaüstü 1280x720 ve 1012x700, koyu/açık, klavye odağı, tam sayfa); `sonra-tr` Türkçe hali.

## Ekranlar

Tek sayfa: ince üst şerit (`FRK-OS // PROJE DİZİNİ` + dil düğmesi) → dev League Gothic ad + giriş +
üç sayaç (depo, test, üretim tarihi) → yapışkan arama/süzgeç çubuğu (mobilde sabitlenmez) →
kategori bölümleri (sarı kare + League Gothic başlık + sayı) → kartlar → altbilgi imzası.

Kart: depo adı (mono, kalın), dil/sürüm/test çipleri, özet, ilk iki özellik, konular, bağlantılar
(Depo, Canlı ya da Oyna, Sürümler). Bağlantı çapaları (`#<depo>`) ve `:target` çerçevesi aynen duruyor.

## Dil kabuğu

Çevrilen: kicker, giriş, sayaç etiketleri, bağlantılar, arama etiketi/ipucu/yer tutucu, süzgeç grup
adları, kategori adları, çip/bağlantı etiketleri (`319 test`, `Depo`, `Sürümler`), durum cümlesi, boş sonuç,
altbilgi. **Çevrilmeyen**: kartların içeriği (özet, özellikler, konular). Bunlar depoların kendi
`project-meta.json` dosyasında İngilizce yazılı; çeviri uydurulmadı. Türkçe modda bunu söyleyen tek satırlık bir not var.
İngilizce metin HTML'de durur, betik yoksa da doğru okunur. Sözlük `sablon.html` içinde; iki dilin anahtar
kümesinin ve her `data-i` anahtarının iki dilde de olması testle kilitli. Kategori adlarının Türkçesi `uret.py` içindeki `GROUPS_TR`.

## Video sisteminden alınanlar

Kaynak: `D:\Claude Projeleri\sosyal\uret\tema.mjs` (Klasik FRK-OS teması) ve `sahne.js`.

| Ne | Nereden | Sayfada |
|---|---|---|
| `#0e0d0b` zemin, `#1a1712` ikinci zemin, `#f1ece2` yazı, `#ffc21a` vurgu | `tema.mjs` → `klasik.akis` | tüm renk belirteçleri; camgöbeği `#19d3e6` ve mercan (video `#ff4d6d`, sayfada koyu zeminde okunurluk için `#ff6b85`) çip renkleri |
| League Gothic başlık, JetBrains Mono etiket | `tema.mjs` → `klasik.font` | h1, bölüm başlıkları, sayaçlar; mono etiketler |
| ızgara dokusu (`doku: "izgara"`) | `tema.mjs` | başlık bölgesinde %5 ızgara, aşağıya doğru solar |
| `iris` geçişi | `sahne.js` GECIS.iris (ortadan büyüyen daire) | açılışta üç sayaç kutusu, 80 ms aralıkla |
| `itme` geçişi (yukarı itme) | `sahne.js` GECIS.itme | eşiği geçen kart 22 px aşağıdan kayarak girer (`expo` benzeri eğri) |
| `flas` | `sahne.js` GECIS.flas | süzgeç/arama değişince sonuç sayacı sarıya parlayıp söner |
| `zoom` | `sahne.js` GECIS.zoom (0,7→1 ölçek) | süzgeç sonrası kartlar 0,96→1 ölçekle yeniden girer |

Alınmayanlar: glitch, bloklar, kararma (okunurluğu bozar ya da ürüne yabancı). Renk akışı (sahne başına
dönen zemin) alınmadı: dizin sayfasında kimlik sakin klasik temadır. Ürünün kimliği ağır bastı: hareket
süsleyicidir, içerik hiçbir şeyi beklemez.

## Hareket kuralları

- Hepsi `@media (prefers-reduced-motion: no-preference)` içinde; betik de `matchMedia` ile bakıyor. Hareket
  tercihi kapalıysa hiç `.pre` sınıfı konmaz, hiçbir animasyon çalışmaz.
- Yalnız `transform`, `opacity`, `clip-path`: yerleşim kayması yok (Lighthouse CLS 0 / 0,001).
- İlk ekrandaki kartlara giriş uygulanmaz (LCP'yi bekletmemek için); geri kalanlar 2,5 sn sonra kaydırılmasa
  da görünür olur (sayfada-bul, ekran görüntüsü). Yazdırırken hepsi görünür.

## Yazı tipleri

Yerel dosyalar, indirme yok, Google Fonts'a bağlantı yok: `assets/fonts/league-gothic.woff2` (8.104 B,
League Gothic 2.001, Latin + Türkçe) ve `assets/fonts/jetbrains-mono.woff2` (37.176 B, JetBrains Mono 2.211,
değişken ağırlık 100–800). İkisi `C:\Users\furki\.cache\hyperframes\fonts\` altındaki, Türkçe karakterleri (Ş Ğ İ ı ç ö ü) içeren alt kümelerden
seçildi (glif haritası ile doğrulandı). Lisans: SIL OFL 1.1, `assets/fonts/OFL.txt`. Yalnız League Gothic ön yüklenir;
ikincisini de ön yüklemek mobil FCP'yi iyileştirmedi (ölçüldü). Yazı tipi eklemenin bedeli: Lighthouse mobil performans 98 → 97 (FCP 1,5 → 1,7 s).

## Kontrast

Ölçülen (tarayıcıda her metin/zemin çifti): koyu tema en düşük 6,46:1, açık tema 5,65:1. Belirteç çiftleri
`tests/test_uret.py` içinde de hesaplanıyor (`text/dim/accent/cyan/coral` × `bg/panel/topic`, ≥ 4,5:1; sarı düğme üstü koyu yazı).
Açık tema (sayfa sistem temasını izliyor): krem `#f1ece2` zemin, koyu kehribar `#7a5600` vurgu.

## Ne değişmedi

Üretici akışı, snapshot (`veri/projeler.json`), feed, sitemap, JSON-LD, çapa davranışı, null kuralı ve
haftalık yenileme. Sosyal kart (`assets/og.*`) eski görselde kaldı: elle yazılmış SVG, sayı içermiyor;
FRK-OS renkleriyle yeniden çizmek ayrı iş.
