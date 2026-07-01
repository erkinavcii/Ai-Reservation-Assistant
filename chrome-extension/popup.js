// Sahibinden AI Rezervasyon Entegrasyonu - Popup Script

document.addEventListener('DOMContentLoaded', () => {
    const activeToggle = document.getElementById('bot-active-toggle');
    const autosendToggle = document.getElementById('autosend-toggle');
    const backendUrlInput = document.getElementById('backend-url');
    const btnSave = document.getElementById('btn-save');
    const statusText = document.getElementById('status-text');

    // Kayıtlı ayarları yükle
    chrome.storage.local.get(['isBotActive', 'isAutoSendEnabled', 'backendUrl'], (result) => {
        if (result.isBotActive !== undefined) {
            activeToggle.checked = result.isBotActive;
        } else {
            activeToggle.checked = true; // Varsayılan aktif
        }

        if (result.isAutoSendEnabled !== undefined) {
            autosendToggle.checked = result.isAutoSendEnabled;
        } else {
            autosendToggle.checked = false; // Varsayılan kapalı (güvenli mod)
        }

        backendUrlInput.value = result.backendUrl || 'http://localhost:8000/chat';
    });

    // Ayarları kaydet
    btnSave.addEventListener('click', () => {
        const isBotActive = activeToggle.checked;
        const isAutoSendEnabled = autosendToggle.checked;
        const backendUrl = backendUrlInput.value.trim();

        chrome.storage.local.set({
            isBotActive,
            isAutoSendEnabled,
            backendUrl
        }, () => {
            statusText.innerText = '✓ Ayarlar başarıyla kaydedildi!';
            setTimeout(() => {
                statusText.innerText = '';
            }, 2500);

            // Açık olan sahibinden.com mesaj sekmesini bulup ayarların güncellendiğini bildirelim
            chrome.tabs.query({ url: '*://www.sahibinden.com/bana-ozel/mesajlar*' }, (tabs) => {
                tabs.forEach(tab => {
                    chrome.tabs.reload(tab.id); // Ayarların taze yüklenmesi için sayfayı yenile
                });
            });
        });
    });
});
