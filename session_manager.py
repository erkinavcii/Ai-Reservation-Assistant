from typing import Dict, List, Any, Optional
import time

class ChatSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        # OpenAI formatindaki mesaj gecmisi
        self.messages: List[Dict[str, str]] = []
        # Tanimlanan rezervasyon parametreleri (hafizada ekstra kontrol veya arayüz icin tutulabilir)
        self.state: Dict[str, Any] = {
            "start_date": None,
            "end_date": None,
            "guest_count": None
        }
        self.last_activity = time.time()

    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        self.last_activity = time.time()
        
        # Hafizayi cok sismemesi icin son 20 mesajla sinirlandiralim (istege bagli)
        if len(self.messages) > 30:
            # Sistem mesajini kaybetmemek icin ilk mesaji koruyup sonrasini kesebiliriz.
            system_msg = [m for m in self.messages if m["role"] == "system"]
            other_msgs = [m for m in self.messages if m["role"] != "system"]
            self.messages = system_msg + other_msgs[-20:]

    def clear(self):
        self.messages = []
        self.state = {
            "start_date": None,
            "end_date": None,
            "guest_count": None
        }
        self.last_activity = time.time()

class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, ChatSession] = {}

    def get_or_create_session(self, session_id: str) -> ChatSession:
        if session_id not in self.sessions:
            self.sessions[session_id] = ChatSession(session_id)
        return self.sessions[session_id]

    def delete_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]

    # Süresi gecen oturumlari temizlemek icin bir yardimci metot
    def cleanup_old_sessions(self, max_idle_seconds: int = 3600):
        now = time.time()
        expired_keys = [
            k for k, v in self.sessions.items()
            if now - v.last_activity > max_idle_seconds
        ]
        for k in expired_keys:
            del self.sessions[k]
