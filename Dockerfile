# Playwright का ऑफिशियल Python इमेज यूज़ कर रहे हैं जिसमें सारे ब्राउज़र्स पहले से इंस्टॉल आते हैं
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# वर्किंग डायरेक्टरी सेट करें
WORKDIR /app

# डिपेंडेंसीज़ कॉपी और इंस्टॉल करें
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# बाकी सारा कोड कॉपी करें
COPY . .

# पोर्ट को एक्सपोज़ करें
EXPOSE 5000

# बॉट और सर्वर को स्टार्ट करने की कमांड (इसके बाद Procfile की ज़रूरत नहीं पड़ेगी)
CMD ["gunicorn", "main:app", "--bind", "0.0.0.0:5000"]
