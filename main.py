import os
import sys
import uvicorn
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from typing import Optional, Dict, Any

# Proje ici moduller
from session_manager import SessionManager
from agent import ReservationAgent
from colorama import Fore, Style, init

init(autoreset=True)

app = FastAPI(
    title="AI Reservation Assistant API",
    description="WhatsApp/Web/Sahibinden kanallarindan gelen mesajlari isleyen AI Rezervasyon Ajanı API.",
    version="1.0.0"
)

# Global yoneticilerimiz
session_manager = SessionManager()
agent = ReservationAgent()

# FastAPI Request/Response Modelleri
class WebhookRequest(BaseModel):
    session_id: str  # Telefon numarasi veya web tarayici session_id'si
    message: str     # Kullanicinin attigi mesaj
    channel: str = "web" # whatsapp, sahibinden, web vb.

class WebhookResponse(BaseModel):
    session_id: str
    response: str
    extracted_state: Dict[str, Any]

@app.post("/chat", response_model=WebhookResponse)
def chat_endpoint(request: WebhookRequest):
    """
    Web, WhatsApp veya Sahibinden gelen mesajlari karsilayacak ana endpoint.
    """
    try:
        session = session_manager.get_or_create_session(request.session_id)
        
        # Ajanin mesaji islemesi
        response_text = agent.process_message(session, request.message)
        
        return WebhookResponse(
            session_id=session.session_id,
            response=response_text,
            extracted_state=session.state
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/session/clear")
def clear_session(session_id: str = Body(..., embed=True)):
    """
    Belirli bir session'in hafizasini ve durumunu sifirlar.
    """
    session = session_manager.get_or_create_session(session_id)
    session.clear()
    return {"status": "success", "message": f"Session '{session_id}' basariyla sifirlandi."}

def run_interactive_cli():
    """
    Gelistiricilerin sistemi terminal uzerinden kolayca test edebilmesi icin etkilesimli CLI.
    """
    print(f"\n{Fore.GREEN}=== AI REZERVASYON ASISTANI CLI TEST EKRANI ==={Style.RESET_ALL}")
    print(f"{Fore.YELLOW}DeepSeek tabanli rezervasyon asistanini canli test edebilirsiniz.{Style.RESET_ALL}")
    print("Oturumu sifirlamak icin: 'clear'")
    print("Cikmak icin: 'exit' yazin.\n")
    
    test_session_id = "test_user_whatsapp_01"
    session = session_manager.get_or_create_session(test_session_id)
    
    while True:
        try:
            user_input = input(f"{Fore.MAGENTA}Siz (WhatsApp/Web): {Style.RESET_ALL}")
            if not user_input.strip():
                continue
                
            if user_input.lower() == 'exit':
                print(f"{Fore.YELLOW}Cikis yapiliyor...{Style.RESET_ALL}")
                break
                
            if user_input.lower() == 'clear':
                session.clear()
                print(f"{Fore.GREEN}[SISTEM] Oturum hafizasi ve rezervasyon parametreleri sifirlandi!{Style.RESET_ALL}\n")
                continue
                
            # Asistanin cevabi
            response = agent.process_message(session, user_input)
            
            print(f"\n{Fore.CYAN}Asistan: {Style.RESET_ALL}{response}")
            
            # Guncel durum
            print(f"{Fore.BLUE}Mevcut Hafiza Durumu: {session.state}{Style.RESET_ALL}\n")
            
        except KeyboardInterrupt:
            print("\nCikis yapiliyor...")
            break
        except Exception as e:
            print(f"{Fore.RED}Bir hata olustu: {e}{Style.RESET_ALL}\n")

if __name__ == "__main__":
    # Eger komut satirindan '--server' parametresi gelirse FastAPI server calissin
    if "--server" in sys.argv:
        port = int(os.getenv("PORT", 8000))
        host = os.getenv("HOST", "0.0.0.0")
        print(f"API Sunucusu baslatiliyor: http://{host}:{port}")
        uvicorn.run(app, host=host, port=port)
    else:
        # Varsayilan olarak kolay test icin CLI modu calisir
        run_interactive_cli()
