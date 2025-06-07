from dotenv import load_dotenv
import os
import requests
import base64

load_dotenv(dotenv_path=".env")
api_key = os.getenv("OPENROUTER_API_KEY")

print("API Key (kontrol):", api_key)

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# 3. Yüklemek istediğin görselin dosya adı
image_path = "pizza.jpeg"  
base64_image = encode_image(image_path)

# 4. OpenRouter API URL ve Header’ları
url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# 5. API’ye gönderilecek istek
payload = {
    "model": "meta-llama/llama-3.2-11b-vision-instruct",
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Lütfen bu görseldeki yemeğin adını belirt. Sadece Türkçe bir yemek ismi ver."
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                }
            ]
        }
    ]
}


# 6. İsteği gönder ve yanıtı yazdır
response = requests.post(url, headers=headers, json=payload)

print("Yanıt:")
print(response.json())


# --- 1. Adım: İlk yanıttan yemek adını çek ---
result = response.json()
yemek_adi = result['choices'][0]['message']['content'].strip()
print(f"Tespit edilen yemek: {yemek_adi}")

# --- 2. Adım: Yeni prompt hazırla ---
kalori_prompt = f"{yemek_adi} adlı yemeğin yaklaşık kalori miktarı nedir? Sadece sayısal bir değer olarak kcal ile birlikte yaz."

payload_kalori = {
    "model": "meta-llama/llama-3.2-11b-vision-instruct",
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": kalori_prompt
                }
            ]
        }
    ]
}

# --- 3. Adım: Yeni istek gönder ---
response_kalori = requests.post(url, headers=headers, json=payload_kalori)
kalori_cevap = response_kalori.json()
print("Tahmini Kalori:")
print(kalori_cevap['choices'][0]['message']['content'].strip())
