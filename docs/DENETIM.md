# Denetim: dizin sayfası (29 Eylül 2026)

Yenilemeden önce, yerelde (`python -m http.server`) çalışan eski sayfa üzerinde ölçüldü. Sonuçlar
gerçek koşulardan; ölçülmeyen bir şey yazılmadı.

## README komutları

| Komut | Sonuç |
|---|---|
| `python3 uret.py --yerel` | çalışıyor: 28 proje, 8 sürüm, sayfa + `feed.xml` + `sitemap.xml` + `robots.txt` |
| `python3 uret.py` (ağdan) | çalışıyor (yalnız geçici bir kopyada denendi; `veri/` bu işte yenilenmedi): 28 proje, 9 sürüm |
| `python3 -m pytest tests -q` | 48 test geçti (yenileme sonrası 62) |
| `python3 -m http.server` → `localhost:8000` | sayfa açılıyor |

Notlar: tam `/meta` koşturulmadı. `pytest` makinede kurulu değildi, geçici bir sanal ortama kuruldu
(depoya bağımlılık eklenmedi). Üretici her koşuda "eski test sayısı" uyarısı basıyor (mcp-vet,
buradane, ai-workflow-engine, mini-creative-toolkit); düzeltmesi o depoların kendi
`project-meta.json` dosyasında, bu işin kapsamı dışında.

## Tarayıcı (Chrome, Playwright; 390x844 mobil, 1280x720 ve 1012x700 masaüstü; koyu ve açık tema)

- Konsol hatası ve uyarısı: **yok**. Yatay kaydırma: **yok** (mobilde de).
- Bağlantı çapaları: `#mcp-vet` kartı açılışta araç çubuğunun altında duruyor ve `:target` ile çerçeveleniyor.
- Klavye: `Tab` sırası atlama bağlantısı, profil bağlantıları, arama, süzgeç düğmeleri; hepsinde 2 px odak halkası. `/` aramaya götürüyor, `Esc` temizliyor.
- Kontrast (her metin/zemin çifti için hesaplandı, WCAG AA 4,5:1; büyük metinde 3:1): koyu tema en düşük **5,33:1**, açık tema en düşük **5,52:1**; başarısız çift yok.
- Süzgeç düğmeleri `aria-pressed` bildiriyor, sonuç sayısı `role="status"` ile okunuyor, arama etiketli.
- Eksik olan: `prefers-reduced-motion` için hiçbir şey yoktu (sayfada hareket de yoktu, yani sorun çıkmıyordu; yeni hareket eklendiği için ölçüt olarak eklendi).

## Lighthouse (yerel sunucu, `lighthouse` 12, Chrome headless; mobilde simüle yavaş 4G)

| | Performans | Erişilebilirlik | Best practices | SEO | FCP | LCP | TBT | CLS | Boyut |
|---|---|---|---|---|---|---|---|---|---|
| Önce, mobil | 98 | **96** | 100 | 100 | 1,5 s | 1,5 s | 10 ms | 0 | 89 KiB |
| Önce, masaüstü | 100 | **96** | 100 | 100 | 0,3 s | 0,3 s | 0 ms | 0 | 89 KiB |

Erişilebilirlikte tek başarısız denetim: `link-in-text-block`. Giriş paragrafındaki ve altbilgideki
bağlantılar yalnızca renkle ayrılıyordu (altı çizili değildi).

## "Ekosistem denetimi" (#19, Furkiozknn/Furkiozknn)

Son yorum 28 Eylül koşusundan; bu depoya ait iki bulgu vardı:

- **Metadata canlı gerçekle ayrışmış (summary ↔ depo açıklaması):** şu an kapalı. Depo açıklaması ile
  `project-meta.json` özeti bire bir aynı (`gh repo view` ile karşılaştırıldı).
- **Yayımlanan test sayısı koşunun yazdığıyla aynı değil (`project-meta.json` 48, `meta-source.json` 37):**
  bu depoda düzeltilecek bir şey yok; doğru sayı depodaki (48, şimdi 62). Fark `meta-source.json` ile profil
  README tablosunda ve meta-source ayrışması kararı Furki'de bekliyor; tam `/meta` koşturulmadı.

Konu bu iş tarafından kapatılmadı: kapatmak workflow'un işi (bulgu kümesi temizlenince kendisi kapatıyor)
ve içinde başka depoların bulguları var.
