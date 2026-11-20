// Vercel serverless function: creates a city guide with Claude.
// Set ANTHROPIC_API_KEY in the Vercel project settings (Environment Variables).
// Optional: ANTHROPIC_MODEL (default claude-sonnet-5-5), ANTHROPIC_VERSION (default 2026-10-21).

const clip = (v, n) => String(v ?? '').slice(0, n);

function buildPrompt({name, country, lat, lng, pop}) {
  return `Sen titiz bir seyahat ve kültür editörüsün. Aşağıdaki şehir için Türkçe, kısa ve doğru bir rehber hazırla.
Şehir: ${name}, ${country} (enlem ${lat}, boylam ${lng}, nüfus yaklaşık ${pop}).
Kurallar:
- Yalnızca genel kabul görmüş, emin olduğun bilgileri yaz. Kesin yılından emin değilsen yüzyıl ya da dönem düzeyinde yaz.
- Yemekler bu şehrin ya da bölgesinin gerçekten bilinen yemekleri olsun; uydurma.
- Şehir küçükse yakın çevredeki (en çok 80 km) öne çıkan yerleri kullanabilirsin.
- Gezilecek yerlerin koordinatları gerçeğe yakın olsun.
- Akıcı, sade Türkçe; abartılı sıfatlar yok.
Yalnızca tek bir JSON nesnesi döndür, başka hiçbir metin yazma:
{"tag":"tek cümlelik tanım","season":"en iyi ziyaret dönemi","days":"önerilen süre (ör. 2 gün)","lang":"konuşulan dil(ler)","cur":"para birimi","tz":"IANA saat dilimi","sig":{"tarih":"en simgesel yıl/dönem, en çok 3 kelime","lezzet":"imza yemek","gezi":"simge yer"},"history":[{"y":"yıl ya da dönem","t":"kısa başlık","d":"1-2 cümle"}],"foods":[{"n":"yemek","k":"tür (ör. Tatlı, Sokak lezzeti, Ana yemek)","d":"1-2 cümle","w":"nerede denenir"}],"places":[{"n":"ad","k":"Tarih|Müze|Çarşı|Manzara|Doğa|Mahalle|Meydan","lat":0,"lng":0,"d":"1 cümle","t":"ziyaret süresi"}],"route":[{"s":"Sabah|Öğle|Öğleden sonra|Akşam","p":0,"d":"1 cümle"}],"tip":"bir yerel ipucu"}
history 4-6 madde, eskiden yeniye. foods tam 4. places 4-6. route 4 adım; p, places dizisindeki sıra numarası (0'dan) ya da null.`;
}

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({error: 'method_not_allowed'});
  if (!process.env.ANTHROPIC_API_KEY) return res.status(503).json({error: 'missing_api_key'});
  const b = req.body || {};
  const city = {name: clip(b.name, 80), country: clip(b.country, 80), lat: Number(b.lat), lng: Number(b.lng), pop: Math.round(Number(b.pop) || 0)};
  if (!city.name || !Number.isFinite(city.lat) || !Number.isFinite(city.lng) || Math.abs(city.lat) > 90 || Math.abs(city.lng) > 180) return res.status(400).json({error: 'bad_request'});
  try {
    const r = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {'x-api-key': process.env.ANTHROPIC_API_KEY, 'anthropic-version': process.env.ANTHROPIC_VERSION || '2026-10-21', 'content-type': 'application/json'},
      body: JSON.stringify({model: process.env.ANTHROPIC_MODEL || 'claude-sonnet-5-5', max_tokens: 4000, messages: [{role: 'user', content: buildPrompt(city)}]})
    });
    if (r.status === 429) return res.status(429).json({error: 'rate_limited'});
    if (!r.ok) return res.status(502).json({error: 'upstream', status: r.status});
    const j = await r.json();
    const text = (j.content || []).map(c => c.text || '').join('');
    const a = text.indexOf('{'), z = text.lastIndexOf('}');
    if (a < 0 || z < a) return res.status(502).json({error: 'invalid_json'});
    const guide = JSON.parse(text.slice(a, z + 1));
    res.setHeader('Cache-Control', 's-maxage=86400, stale-while-revalidate=604800');
    return res.status(200).json(guide);
  } catch (e) {
    return res.status(502).json({error: 'upstream'});
  }
}
