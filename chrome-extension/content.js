// Sahibinden AI Rezervasyon Entegrasyonu - Content Script
console.log("🤖 Sahibinden AI Rezervasyon Eklentisi Yüklendi!");

// Varsayılan CSS Seçiciler (Sahibinden.com DOM yapısına göre güncellenebilir)
const SELECTORS = {
    chatContainer: '.messaging-details-area', // Mesaj detay alanı
    messageRows: '.message-item', // Her bir mesaj satırı
    incomingClass: 'incoming', // Gelen mesajı belirten sınıf adı (veya kontrol mekanizması)
    messageText: '.message-text', // Mesaj metni element seçici
    textarea: 'textarea#messageText, textarea.chat-input, .messaging-input-area textarea', // Mesaj yazma kutusu
    sendButton: '.send-button, .messaging-input-area button, button[type="submit"]', // Gönder butonu
    usernameHeader: '.chat-partner-name, .messaging-title-area h3' // Konuşulan kişinin adı
};

// Global Durum
let isBotActive = true;
let isAutoSendEnabled = false; // Güvenlik amacıyla varsayılan olarak kapalı (Yarı otomatik / Copilot modu)
let backendUrl = "http://localhost:8000/chat";
let lastProcessedMessageId = "";

// Chrome Storage'dan ayarları yükle
function loadSettings() {
    chrome.storage.local.get(['isBotActive', 'isAutoSendEnabled', 'backendUrl'], (result) => {
        if (result.isBotActive !== undefined) isBotActive = result.isBotActive;
        if (result.isAutoSendEnabled !== undefined) isAutoSendEnabled = result.isAutoSendEnabled;
        if (result.backendUrl !== undefined) backendUrl = result.backendUrl;
        
        console.log("🤖 Ayarlar Yüklendi:", { isBotActive, isAutoSendEnabled, backendUrl });
        updateControlUI();
    });
}

// Sayfaya Kontrol Arayüzü Ekle (Görsel Denetim)
function injectControlUI() {
    // Eğer zaten eklendiyse tekrar ekleme
    if (document.getElementById('ai-bot-control-panel')) return;

    const chatHeader = document.querySelector(SELECTORS.usernameHeader);
    if (!chatHeader) return;

    const panel = document.createElement('div');
    panel.id = 'ai-bot-control-panel';
    panel.style.display = 'flex';
    panel.style.alignItems = 'center';
    panel.style.gap = '15px';
    panel.style.backgroundColor = '#f1f3f4';
    panel.style.padding = '8px 12px';
    panel.style.borderRadius = '20px';
    panel.style.marginLeft = '15px';
    panel.style.fontSize = '12px';
    panel.style.fontFamily = 'Arial, sans-serif';
    panel.style.border = '1px solid #dadce0';
    panel.style.color = '#3c4043';
    panel.style.zIndex = '9999';

    panel.innerHTML = `
        <div style="display:flex; align-items:center; gap:5px;">
            <input type="checkbox" id="ai-active-checkbox" ${isBotActive ? 'checked' : ''} style="cursor:pointer;">
            <label for="ai-active-checkbox" style="font-weight:bold; cursor:pointer;">AI Asistan Aktif</label>
        </div>
        <div style="display:flex; align-items:center; gap:5px;">
            <input type="checkbox" id="ai-autosend-checkbox" ${isAutoSendEnabled ? 'checked' : ''} style="cursor:pointer;">
            <label for="ai-autosend-checkbox" style="font-weight:bold; color:#d93025; cursor:pointer;">Oto-Gönder (Tehlikeli!)</label>
        </div>
        <span id="ai-status-badge" style="font-weight:bold; color:#188038;">● Hazır</span>
    `;

    // Header'ın yanına ekle
    chatHeader.parentElement.appendChild(panel);

    // Event Listener'lar
    document.getElementById('ai-active-checkbox').addEventListener('change', (e) => {
        isBotActive = e.target.checked;
        chrome.storage.local.set({ isBotActive });
        showStatus(isBotActive ? "Hazır" : "Devre Dışı", isBotActive ? "#188038" : "#70757a");
    });

    document.getElementById('ai-autosend-checkbox').addEventListener('change', (e) => {
        isAutoSendEnabled = e.target.checked;
        chrome.storage.local.set({ isAutoSendEnabled });
    });
}

function updateControlUI() {
    const activeCb = document.getElementById('ai-active-checkbox');
    const autoCb = document.getElementById('ai-autosend-checkbox');
    if (activeCb) activeCb.checked = isBotActive;
    if (autoCb) autoCb.checked = isAutoSendEnabled;
    showStatus(isBotActive ? "Hazır" : "Devre Dışı", isBotActive ? "#188038" : "#70757a");
}

function showStatus(text, color) {
    const badge = document.getElementById('ai-status-badge');
    if (badge) {
        badge.innerText = `● ${text}`;
        badge.style.color = color;
    }
}

// Mesaj Kontrol ve AI Akışı
function checkNewMessages() {
    if (!isBotActive) return;

    const chatContainer = document.querySelector(SELECTORS.chatContainer);
    if (!chatContainer) return;

    // Arayüz panelini enjekte et (yoksa)
    injectControlUI();

    const messages = document.querySelectorAll(SELECTORS.messageRows);
    if (messages.length === 0) return;

    const lastMessageRow = messages[messages.length - 1];
    
    // Mesajın benzersiz bir ID'si veya içeriğine göre hash oluştur
    const messageId = lastMessageRow.innerText + "_" + messages.length;
    
    // Eğer son mesajı zaten işlediysek dur
    if (messageId === lastProcessedMessageId) return;

    // Gelen mesaj mı (sol taraftaki mesaj balonları)?
    // Genelde gelen mesajlar sağa yaslı olmayanlar veya class listesinde 'incoming', 'partner' vb. olanlardır.
    const isIncoming = lastMessageRow.classList.contains(SELECTORS.incomingClass) || 
                       lastMessageRow.getAttribute('data-direction') === 'in' || 
                       !lastMessageRow.classList.contains('outgoing') && !lastMessageRow.classList.contains('self');

    if (isIncoming) {
        lastProcessedMessageId = messageId;
        
        const messageTextEl = lastMessageRow.querySelector(SELECTORS.messageText);
        if (!messageTextEl) return;
        const messageContent = messageTextEl.innerText.trim();

        // Konuşulan kişinin adını al
        const usernameEl = document.querySelector(SELECTORS.usernameHeader);
        const username = usernameEl ? usernameEl.innerText.trim().replace(/\s+/g, '_') : "sahibinden_user";

        console.log(`🤖 Yeni Gelen Mesaj [${username}]: "${messageContent}"`);
        processWithAI(username, messageContent);
    }
}

// AI Backend'ine İstek Gönderme
function processWithAI(username, message) {
    showStatus("AI Düşünüyor...", "#1a73e8");

    fetch(backendUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            session_id: `sahibinden_${username}`,
            message: message,
            channel: "sahibinden"
        })
    })
    .then(response => {
        if (!response.ok) throw new Error("Backend hatası: " + response.statusText);
        return response.json();
    })
    .then(data => {
        console.log("🤖 AI Yanıtı:", data);
        writeResponseToTextarea(data.response);
        showStatus("Yanıt Hazır", "#188038");
    })
    .catch(err => {
        console.error("❌ AI Bağlantı Hatası:", err);
        showStatus("AI Hata Aldı", "#d93025");
    });
}

// Metin Kutusuna Yazma ve Tetikleme
function writeResponseToTextarea(replyText) {
    const textarea = document.querySelector(SELECTORS.textarea);
    if (!textarea) {
        console.warn("⚠️ Mesaj textarea'sı bulunamadı!");
        return;
    }

    textarea.value = replyText;
    
    // React / Angular input eventlerini tetiklemek için elzemdir
    textarea.dispatchEvent(new Event('input', { bubbles: true }));
    textarea.dispatchEvent(new Event('change', { bubbles: true }));
    
    // Yüksekliği otomatik ayarla (varsa sahibinden iç fonksiyonu için)
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';

    if (isAutoSendEnabled) {
        const sendBtn = document.querySelector(SELECTORS.sendButton);
        if (sendBtn) {
            console.log("🚀 Oto-gönderim tetikleniyor...");
            setTimeout(() => {
                sendBtn.click();
                showStatus("Yanıt Gönderildi", "#188038");
            }, 1000);
        } else {
            console.warn("⚠️ Gönder butonu bulunamadı!");
        }
    } else {
        // Kullanıcı onaylayıp gönder butonuna kendisi basacak
        showStatus("Gönderim Bekleniyor", "#f9ab00");
        
        // Kutuyu belirginleştir
        textarea.style.border = "2px solid #f9ab00";
        textarea.style.backgroundColor = "#fffdf4";
    }
}

// Sayfa Değişikliklerini MutationObserver ile İzleme
let currentUrl = location.href;
const pageObserver = new MutationObserver(() => {
    // URL değiştiğinde (başka bir chata geçildiğinde) sıfırla
    if (location.href !== currentUrl) {
        currentUrl = location.href;
        lastProcessedMessageId = "";
        console.log("🤖 Sohbet odası değişti, dinleme sıfırlandı.");
    }
    checkNewMessages();
});

// Sayfa gövdesini dinle
pageObserver.observe(document.body, {
    childList: true,
    subtree: true
});

// İlk Yükleme
loadSettings();
setInterval(checkNewMessages, 2000); // Ek güvenlik için polling
