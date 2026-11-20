# kâşif · sokak seviyesinde dünya haritası

3D küre olarak açılan, sokak ve bina seviyesine kadar yakınlaşan bir dünya haritası.
Harita MapLibre GL JS ile çiziliyor, harita verisi OpenFreeMap'ten geliyor (OpenStreetMap tabanlı, ücretsiz, API anahtarı yok).

## Neler var

- Küreden sokağa kesintisiz yakınlaşma, Türkçe yer adları (varsa), 3B binalar (3B butonu)
- 14 elle hazırlanmış şehir rehberi: tarih çizelgesi, mutfak, gezilecek yerler, 1 günlük rota
  - Gezilecek bir yere tıklayınca harita o noktaya 3B olarak uçar
- 7.400+ şehir: herhangi birine tıklayınca bilgi kartı; Vercel kurulumu varsa "Rehberi hazırla" ile Claude rehber yazar
- Ülke sayfaları, filtreli arama ve OpenStreetMap adres araması
- Gün gün gezi planlayıcı, "Şehri bul" oyunu, gezgin pasaportu, konumuma git

## Dosyalar

```
index.html            uygulamanın tamamı
data/                 şehirler, ülke sınırları, ülke bilgileri
api/guide.js          canlı rehber için Vercel sunucu fonksiyonu
package.json          Vercel için (ESM)
```

## Bilgisayarında denemek

`index.html` dosyasına çift tıklamak yetmez; veriler `fetch` ile okunduğu için küçük bir sunucu gerekir.
Bu klasörün içinde:

```
npx serve .
# ya da
python3 -m http.server 8000
```

Sonra tarayıcıda `http://localhost:8000` (veya `serve`'ün verdiği adres). Bu modda "Rehberi hazırla" çalışmaz, geri kalan her şey çalışır.

## Yayınlama seçenek 1: Vercel (önerilen, canlı rehber dahil)

1. Bu klasörü bir GitHub deposuna yükle.
2. vercel.com → Add New → Project → depoyu seç. Klasör deponun içinde bir alt klasördeyse **Root Directory** olarak onu seç.
3. **Environment Variables** kısmına ekle:
   - `ANTHROPIC_API_KEY` = Claude Console'dan aldığın API anahtarı
   - (isteğe bağlı) `ANTHROPIC_MODEL` — varsayılan `claude-sonnet-5-5`
4. Deploy. Site `https://proje-adin.vercel.app` adresinde açılır.

Önemli: `/api/guide` herkese açık bir adres. Siteyi paylaşırsan başkaları da rehber oluşturabilir ve bu senin API kullanımına yazılır.
Claude Console'da harcama limiti koy; site büyürse istek sınırlaması (rate limit) ekle.

## Yayınlama seçenek 2: GitHub Pages (ücretsiz, canlı rehber yok)

1. Klasörü bir GitHub deposuna yükle.
2. Settings → Pages → Branch: `main`, klasör: `/ (root)` → Save.
3. Birkaç dakika sonra `https://kullanici-adin.github.io/depo-adin/` adresinde açılır.

GitHub Pages sunucu kodu çalıştıramadığı için "Rehberi hazırla" butonu bilgi mesajı gösterir.

## Notlar

- Harita stili: `index.html` içindeki `STYLE_URL` (varsayılan OpenFreeMap "positron"). Renkler `palette()` fonksiyonunda.
- OpenFreeMap ve OpenStreetMap atıfları sağ altta otomatik görünür, kaldırma.
- Adres araması OpenStreetMap Nominatim'i kullanır. Bu ücretsiz servis yoğun kullanım için değil; site büyürse kendi arama servisini kullan.
- Claude'un yazdığı rehberler doğrulanmamıştır ve kullanıcının tarayıcısında saklanır.
