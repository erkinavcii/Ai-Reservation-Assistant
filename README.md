# 🤖 Yapay Zeka Rezervasyon Asistanı (DeepSeek Agent)

Bu proje; WhatsApp, Web Chat veya sahibinden.com gibi kanallardan gelen rezervasyon taleplerini doğal dilde karşılayan, eksik parametreleri (Giriş Tarihi, Çıkış Tarihi, Kişi Sayısı) tamamlatıp ardından backend API'niz (`check_reservation_status`) ile konuşan bir **Yapay Zeka Rezervasyon Asistanı (Agent)** projesidir.

Projede LLM motoru olarak **DeepSeek-V4-Flash / DeepSeek-V4-Pro** modelleri (OpenAI uyumlu API formatında) kullanılmıştır.

---

## 🛠️ Mimari ve Nasıl Çalışır?

Asistan, deterministik kurallar ile LLM'in esnekliğini birleştiren bir yapıya sahiptir:

1. **Eksik Parametre Kontrolü (Slot Filling):** Sistem promptunda belirlenen katı kurallarla, asistan `giriş tarihi`, `çıkış tarihi` ve `kişi sayısı` parametrelerinin tamamına sahip olmadan API çağrısı (Tool Call) yapmaz. Eksik parametreleri kullanıcıdan doğal dille ister.
2. **Doğal Dil Tarih Çözümleme:** Kullanıcının "haftaya cuma", "Ağustos ortası", "15-20 Ağustos" gibi ifadelerini, asistan sistem saatini (`Bugünün Tarihi`) baz alarak `YYYY-MM-DD` biçimine çevirir.
3. **Müsaitlik & Alternatif Yönetimi (Tool Calling):** Tüm parametreler toplandığında asistan `check_reservation_status` aracını tetikler:
   * **Müsaitse:** Toplam fiyatı ve para birimini alıp kullanıcıya sunar, rezervasyon isteyip istemediğini sorar.
   * **Doluysa:** Backend'den dönen alternatif tarih ve fiyatları analiz edip müşteriye alternatifli teklifler sunar.
4. **Hafıza ve Oturum Yönetimi (Session Memory):** WhatsApp veya Sahibinden gibi kanallar durumsuz (stateless) olduğundan, her bir kullanıcı (örneğin telefon numarası) için `ChatSession` nesnesi oluşturulup konuşma geçmişi hafızada tutulur.

---

## 📂 Proje Yapısı

* [requirements.txt](file:///c:/Users/Administrator/Desktop/Projelerim/AI-reservation-assistant/requirements.txt): Gerekli kütüphaneler.
* [.env](file:///c:/Users/Administrator/Desktop/Projelerim/AI-reservation-assistant/.env): DeepSeek API Key ve yapılandırma bilgileri.
* [config.py](file:///c:/Users/Administrator/Desktop/Projelerim/AI-reservation-assistant/config.py): API bağlantısı ve yapılandırma yönetimi.
* [mock_backend.py](file:///c:/Users/Administrator/Desktop/Projelerim/AI-reservation-assistant/mock_backend.py): Tesisinizin doluluk kurallarını ve alternatif tarihlerini üreten simüle edilmiş API katmanı.
* [session_manager.py](file:///c:/Users/Administrator/Desktop/Projelerim/AI-reservation-assistant/session_manager.py): Telefon numarası / Session ID bazlı konuşma geçmişi ve durum (state) yöneticisi.
* [agent.py](file:///c:/Users/Administrator/Desktop/Projelerim/AI-reservation-assistant/agent.py): DeepSeek arayüzü, sistem promptları ve Tool Calling mekanizması.
* [main.py](file:///c:/Users/Administrator/Desktop/Projelerim/AI-reservation-assistant/main.py): Test için etkileşimli CLI arayüzü ve API entegrasyonları için FastAPI Webhook sunucusu.

---

## 🚀 Başlangıç

### 1. Kurulum ve Bağımlılıklar
İlk olarak terminalde gerekli paketleri yükleyin:
```bash
pip install -r requirements.txt
```

### 2. Yapılandırma (`.env`)
Proje kök dizinindeki `.env` dosyasını açıp kendi **DeepSeek API Key** bilginizi tanımlayın:
```env
DEEPSEEK_API_KEY=your_real_deepseek_api_key
```

### 3. Etkileşimli CLI ile Test Etme (Hızlı Başlangıç)
FastAPI sunucusunu başlatmadan önce asistanın eksik parametreleri nasıl kovaladığını terminal üzerinden canlı olarak test edebilirsiniz:
```bash
python main.py
```
*Bu modda asistanla doğrudan WhatsApp'taymış gibi yazışabilirsiniz. Oturumu sıfırlamak için `clear`, çıkmak için `exit` yazmanız yeterlidir.*

### 4. API Sunucusu (FastAPI Webhook) Olarak Çalıştırma
Üretim ortamında veya test webhook entegrasyonlarında API'yi sunucu modunda ayağa kaldırmak için:
```bash
python main.py --server
```
Varsayılan olarak sunucu `http://127.0.0.1:8000` adresinde başlayacaktır. API dökümantasyonunuza `http://127.0.0.1:8000/docs` adresinden erişebilirsiniz.

---

## 🛜 Webhook API Kullanım Örneği

Asistanınızı WhatsApp (örn. Twilio Webhook veya Meta Cloud) ya da web sitenizin chat balonuna bağlamak için `/chat` endpoint'ine POST isteği atmanız yeterlidir:

**İstek (POST `/chat`):**
```json
{
  "session_id": "+905551234567",
  "message": "Ağustos'un ilk haftası 4 kişi gelmek istiyoruz, yeriniz var mı?",
  "channel": "whatsapp"
}
```

**Modelin API'yi Tetikleme ve Yanıt Süreci (Arka Planda):**
1. Ajan bugün tarihine bakar, "Ağustos ilk haftası" -> `2026-08-01` - `2026-08-07` aralığını tespit eder.
2. Misafir sayısı `4` belirlenmiştir.
3. 3 zorunlu parametre de tam olduğu için `check_reservation_status` aracını tetikler.
4. Mock backend bu tarih aralığı dolu olduğu için alternatif tarihleri döner.
5. Ajan alternatifleri analiz edip kullanıcıya şu şekilde doğal dilde cevap döner:

**Yanıt:**
```json
{
  "session_id": "+905551234567",
  "response": "Merhaba! 🌸 İstediğiniz 1 - 7 Ağustos tarihleri arasında tesisimiz maalesef doludur. Ancak sizleri ağırlamayı çok isteriz! 😊 Aynı süre için şu alternatif tarihlerimiz uygundur:\n\n📅 **15 - 22 Ağustos** (Fiyat: 20.000 TL)\n📅 **25 Temmuz - 1 Ağustos** (Fiyat: 19.000 TL)\n\nBu alternatif tarihlerden biri sizin için uygun olur mu? Hangi aralığı tercih edersiniz? 🏡✨",
  "extracted_state": {
    "start_date": "2026-08-01",
    "end_date": "2026-08-07",
    "guest_count": 4
  }
}
```
