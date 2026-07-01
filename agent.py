import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from config import get_openai_client, DEEPSEEK_MODEL
from session_manager import ChatSession
import mock_backend
from colorama import Fore, Style, init

# Initialize colorama for beautiful CLI logging
init(autoreset=True)

# Definition of the check_reservation_status tool for DeepSeek
RESERVATION_TOOL = {
    "type": "function",
    "function": {
        "name": "check_reservation_status",
        "description": (
            "Belirtilen tarihler ve kisi sayisi icin tesisin musaitlik durumunu ve fiyatini kontrol eder. "
            "Giris tarihi, cikis tarihi ve misafir sayisi parametrelerinin TAMAMI saglanmadan bu tool cagrilmamalidir. "
            "Eksik parametre varsa, tool cagirmak yerine kullaniciya eksik parametreleri sorun."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Giris tarihi (Format: YYYY-MM-DD)"
                },
                "end_date": {
                    "type": "string",
                    "description": "Cikis tarihi (Format: YYYY-MM-DD)"
                },
                "guest_count": {
                    "type": "integer",
                    "description": "Toplam misafir sayisi"
                }
            },
            "required": ["start_date", "end_date", "guest_count"]
        }
    }
}

def get_system_prompt() -> str:
    """Dinamik olarak bugunun tarihini iceren sistem promptunu uretir."""
    today = datetime.now().strftime("%Y-%m-%d")
    return f"""Sen, Villa Natura Turizm Tesisimiz için çalışan profesyonel, cana yakın ve kibar bir Yapay Zeka Rezervasyon Asistanısın (Agent).
Görevin, müşterilerin rezervasyon taleplerini toplamak, müsaitlik kontrolü yapmak ve onları rezervasyona yönlendirmektir.

Bugünün Tarihi: {today} (Tarih hesaplamalarını bu güne göre yapmalısın. Örneğin 'haftaya cuma' denirse bugünden itibaren hesapla).

KURALLAR:
1. Müsaitlik kontrolü yapabilmek için şu 3 parametrenin TAMAMI zorunludur:
   - Giriş Tarihi (start_date) - YYYY-MM-DD formatında olmalı.
   - Çıkış Tarihi (end_date) - YYYY-MM-DD formatında olmalı.
   - Kişi Sayısı (guest_count) - Integer olmalı.
2. EĞER BU 3 BİLGİDEN BİRİ BİLE EKSİKSE, 'check_reservation_status' ARACINI KESİNLİKLE ÇAĞIRMA. Eksik olan parametreyi/parametreleri kullanıcıdan kibarca iste.
   Örnek: Kullanıcı "15-20 Ağustos müsait mi?" yazdıysa, misafir sayısını öğrenmeden aracı çağırma. Önce misafir sayısını sor.
   Örnek: Kullanıcı "4 kişi geleceğiz" yazdıysa, tarih aralığını öğrenmeden aracı çağırma. Net tarih aralığını sor.
3. Kullanıcı "Temmuz ayı", "bayram dönemi", "eylülün ilk haftası" gibi genel veya doğal dilde tarihler belirtirse, o tarihlerin hangi günlere denk geldiğini bugünün tarihini ({today}) baz alarak hesapla ve kullanıcıya "x-y tarihleri arası mı?" diye teyit et veya net tarih iste.
4. Tesis doluysa (is_available = False dönerse), sana API'dan gelen alternatif tarihleri ve fiyatları doğal ve ikna edici bir dille müşteriye sun. Alternatifleri teklif et.
5. Kullanıcı rezervasyon dışı sorular sorarsa, şu genel tesis bilgilerini kullanarak cevap ver:
   - Evcil hayvan: Kabul ediliyor (Ekstra 1.500 TL temizlik ücreti vardır).
   - Havuz: Tam korunaklıdır, dışarıdan görünmez (Muhafazakar ailelere uygundur).
   - Denize uzaklık: 800 metre (Yürüme mesafesinde).
   - Kahvaltı: Dahil değildir, ancak villada tam donanımlı mutfak mevcuttur.
6. Mesajların WhatsApp veya Sahibinden formatına uygun olarak kısa, net ve emojilerle zenginleştirilmiş olsun. Çok uzun paragraflar yazma.
"""

class ReservationAgent:
    def __init__(self):
        self.client = get_openai_client()

    def process_message(self, session: ChatSession, user_message: str) -> str:
        """Kullanici mesajini isler ve DeepSeek modelini kullanarak cevap doner."""
        print(f"\n[AGENT LOG] Session ID: {Fore.CYAN}{session.session_id}{Style.RESET_ALL} | Girdi: {Fore.YELLOW}'{user_message}'{Style.RESET_ALL}")
        
        # Eger oturum yeni ise sistem mesajini en basa ekleyelim
        if not session.messages:
            session.messages.append({"role": "system", "content": get_system_prompt()})
        else:
            # Sistem promptunu güncel tarih icerecek sekilde guncelleyelim (istege bagli)
            session.messages[0] = {"role": "system", "content": get_system_prompt()}

        # Kullanicinin yeni mesajini gecmise ekle
        session.add_message("user", user_message)

        # DeepSeek API'sini cagir
        return self._call_deepseek_with_tools(session)

    def _call_deepseek_with_tools(self, session: ChatSession, depth: int = 0) -> str:
        # Sonsuz dongu korumasi (en fazla 3 ardisik tool cagrisina izin verelim)
        if depth > 3:
            print(f"{Fore.RED}[AGENT ERROR] Maksimum tool cagrisi derinligine ulasildi.{Style.RESET_ALL}")
            return "Rezervasyon sistemimizde gecici bir aksaklik yasaniyor. Lutfen biraz sonra tekrar deneyin."

        try:
            print(f"[AGENT LOG] DeepSeek modeline istek atiliyor ({DEEPSEEK_MODEL})...")
            response = self.client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=session.messages,
                tools=[RESERVATION_TOOL],
                tool_choice="auto",
                temperature=0.3  # Rezervasyon kararlarinda daha tutarli olması icin dusuk sicaklik
            )
        except Exception as e:
            print(f"{Fore.RED}[AGENT ERROR] DeepSeek API hatasi: {e}{Style.RESET_ALL}")
            # API Key hatasi uyarisi
            if "sk-placeholder" in str(e) or "api_key" in str(e).lower() or "401" in str(e):
                return "⚠️ Hata: Lütfen geçerli bir DeepSeek API anahtarı girin. Proje dizinindeki `.env` dosyasını düzenleyebilirsiniz."
            return "Sistemimizde su anda bir baglanti sorunu var, size birazdan yardimci olacagim."

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        # Eger model bir tool cagirmak istedi ise
        if tool_calls:
            # Modelin tool cagrisini mesaja donusturup gecmise ekleyelim
            session.messages.append(response_message)

            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                print(f"[AGENT LOG] Model Tool Tetikledi: {Fore.GREEN}{function_name}{Style.RESET_ALL} ile argümanlar: {Fore.GREEN}{function_args}{Style.RESET_ALL}")
                
                if function_name == "check_reservation_status":
                    # Parametreleri guvenli sekilde alalim
                    start_date = function_args.get("start_date")
                    end_date = function_args.get("end_date")
                    guest_count = function_args.get("guest_count")
                    
                    # Session state guncelle
                    session.state["start_date"] = start_date
                    session.state["end_date"] = end_date
                    session.state["guest_count"] = guest_count
                    
                    # Mock backend'i cagir
                    api_result = mock_backend.check_reservation_status(
                        start_date=start_date,
                        end_date=end_date,
                        guest_count=int(guest_count) if guest_count else 0
                    )
                    
                    print(f"[AGENT LOG] API Yaniti: {Fore.BLUE}{api_result}{Style.RESET_ALL}")
                    
                    # Tool sonucunu mesaj gecmisine ekle
                    session.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": json.dumps(api_result)
                    })
            
            # Guncellenmis gecmis ile modeli tekrar cagir (Recursive)
            return self._call_deepseek_with_tools(session, depth + 1)
        
        # Tool cagrisi yoksa, bu final yanittir
        assistant_reply = response_message.content
        if assistant_reply:
            session.add_message("assistant", assistant_reply)
            return assistant_reply
        
        return "Size nasil yardimci olabilirim?"
