from datetime import datetime, timedelta
from typing import Dict, Any, List

def check_reservation_status(start_date: str, end_date: str, guest_count: int) -> Dict[str, Any]:
    """
    Belirtilen tarihler ve kisi sayisi icin tesisin musaitlik durumunu kontrol eder.
    
    start_date: 'YYYY-MM-DD' formatinda giris tarihi
    end_date: 'YYYY-MM-DD' formatinda cikis tarihi
    guest_count: Misafir sayisi
    """
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return {
            "error": "Gecersiz tarih formati. Tarihler YYYY-MM-DD formatinda olmalidir."
        }

    if start >= end:
        return {
            "error": "Gelis tarihi, donus tarihinden once olmalidir."
        }

    day_count = (end - start).days

    # Mock Doluluk Senaryosu:
    # Varsayalim ki 1 Agustos 2026 - 15 Agustos 2026 tarihleri arasinda tesis tamamen dolu.
    busy_start = datetime.strptime("2026-08-01", "%Y-%m-%d")
    busy_end = datetime.strptime("2026-08-15", "%Y-%m-%d")

    # Cakisma kontrolü
    # Eger aranan aralik dolu araliga denk geliyorsa dolu donelim.
    overlap = max(start, busy_start) < min(end, busy_end)

    # Kisi sayisi limiti: Maksimum 6 kisi kabul ediyoruz
    if guest_count > 6:
        return {
            "is_available": False,
            "reason": "Tesisimiz tek seferde maksimum 6 misafir kabul edebilmektedir.",
            "alternatives": [
                {
                    "start_date": start_date,
                    "end_date": end_date,
                    "total_price": day_count * 5000,
                    "currency": "TRY",
                    "note": "2 oda seklinde ayri rezervasyon yapabilirsiniz."
                }
            ]
        }

    if overlap:
        # Doluysa alternatif tarihler sunalim
        # Alternatif 1: Dolu donemin hemen sonrasi
        alt1_start = busy_end
        alt1_end = alt1_start + timedelta(days=day_count)
        
        # Alternatif 2: Dolu donemin hemen oncesi
        alt2_start = busy_start - timedelta(days=day_count)
        alt2_end = busy_start

        # Fiyatlandirma (kisi basi gunluk 1500 TL baz fiyat + 2000 TL sabit temizlik)
        price_per_day = 1500 * guest_count
        base_price = (day_count * price_per_day) + 2000

        return {
            "is_available": False,
            "reason": f"{start_date} ile {end_date} tarihleri arasinda tesisimiz doludur.",
            "alternatives": [
                {
                    "start_date": alt1_start.strftime("%Y-%m-%d"),
                    "end_date": alt1_end.strftime("%Y-%m-%d"),
                    "total_price": int(base_price),
                    "currency": "TRY"
                },
                {
                    "start_date": alt2_start.strftime("%Y-%m-%d"),
                    "end_date": alt2_end.strftime("%Y-%m-%d"),
                    "total_price": int(base_price * 0.95),  # Erken veya alternatif icin ufak bir indirim simülasyonu
                    "currency": "TRY"
                }
            ]
        }
    else:
        # Musaitse fiyatlandirma hesapla
        price_per_day = 1800 * guest_count
        total_price = (day_count * price_per_day) + 2500
        return {
            "is_available": True,
            "total_price": int(total_price),
            "currency": "TRY"
        }
