"""
Görsel promptu (GPT-4.1-mini) ve Görsel Üretimi (Kie AI).
n8n'deki "Görsel Prompt", "HTTP Request (Kie AI)" ve "Download Image" node'ları.
"""
from ops_logger import get_ops_logger
ops = get_ops_logger("LinkedIn_Text_Paylasim", "ImageGenerator")
import os
import requests
import tempfile
import time
from openai import OpenAI

from config import settings


class ImageGenerator:
    """Metinden görsel promptu çıkarır ve Kie AI ile görsel üretir."""

    def __init__(self):
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def generate_post_image(self, post_text: str) -> str:
        """
        1. GPT-4.1-mini ile görsel promptu üretir.
        2. Kie AI API'sine istek atar.
        3. Üretilen görseli temp klasörüne indirir.
        
        Returns:
            İndirilen görselin lokal dosya yolu.
        """
        if settings.IS_DRY_RUN:
            ops.info("[DRY-RUN] Görsel prompt üretme atlanıyor.")
            ops.info("[DRY-RUN] Kie AI görsel üretme atlanıyor.")
            return None

        # Step 1: Prompt Üretimi (GPT-4o-mini)
        prompt = self._generate_image_prompt(post_text)

        # Step 2 & 3: Kie AI ile Üret ve İndir
        image_path = self._generate_and_download_from_kie(prompt)
        return image_path

    def _generate_image_prompt(self, post_text: str) -> str:
        """Post metninden İngilizce görsel promptu çıkarır."""
        system_message = (
            "You are an expert AI image prompt engineer. Your job is to read the "
            "following LinkedIn post and create a highly detailed, descriptive, "
            "and compelling image generation prompt in English that perfectly "
            "captures the essence of the post. The image should be professional, "
            "modern, and visually engaging, suitable for a LinkedIn audience."
        )

        user_message = (
            f"Here is the LinkedIn post:\n\n{post_text}\n\n"
            "Create a vivid image generation prompt based on this post. "
            "Output ONLY the prompt text, nothing else."
        )

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7
            )
            prompt = response.choices[0].message.content.strip()
            ops.info(f"Görsel promptu üretildi ({len(prompt)} karakter)")
            return prompt
        except Exception as e:
            ops.error(f"Görsel prompt üretme hatası: {e}", exception=e)
            raise

    def _generate_and_download_from_kie(self, prompt: str) -> str:
        """
        Kie AI API kullanarak görsel üretir ve TaskID ile polling yaparak sonucu indirir.
        Görsel formatı 16:9 olacak şekilde ayarlanır.
        """
        url = "https://api.kie.ai/v1/task/image"
        headers = {
            "Authorization": f"Bearer {settings.KIE_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # aspect_ratio parametresini düzelt: "16:9" formatında olmalı.
        payload = {
            "model": "nano-banana-2",
            "prompt": prompt,
            "aspect_ratio": "16:9"
        }

        try:
            # 1. Task Oluşturma
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if data.get("status") != 0:
                error_msg = data.get('error', 'Bilinmeyen Kie API hatası')
                ops.error("Kie AI Task oluşturma başarısız", message=error_msg)
                raise Exception(f"Kie API Error: {error_msg}")
            
            task_id = data.get("data", {}).get("task_id")
            if not task_id:
                ops.error("Kie AI Task ID alınamadı", message=str(data))
                raise Exception("Kie API yanıtında task_id bulunamadı")
                
            ops.info(f"Kie AI Task oluşturuldu: {task_id}")
            
            # 2. Polling ile durumu kontrol etme
            poll_url = f"https://api.kie.ai/v1/task/image/{task_id}"
            max_retries = 30
            retry_count = 0
            
            while retry_count < max_retries:
                time.sleep(5)  # Her 5 saniyede bir kontrol et
                poll_resp = requests.get(poll_url, headers=headers, timeout=10)
                poll_resp.raise_for_status()
                poll_data = poll_resp.json()
                
                status_code = poll_data.get("status")
                # 0 = işleniyor, 1 = tamamlandı
                if status_code == 1:
                    # Görev tamamlandı, resim URL'sini al
                    task_data = poll_data.get("data", {})
                    images = task_data.get("images", [])
                    image_url = images[0] if images else task_data.get("image_url")
                    
                    if not image_url:
                        ops.error("Kie AI Görsel URL'i alınamadı", message=str(poll_data))
                        raise Exception("Kie API tamamlandı ancak görsel URL'i bulunamadı")
                        
                    ops.info(f"Görsel üretildi, URL alındı: {image_url}")
                    
                    # 3. Görseli İndir
                    img_response = requests.get(image_url, timeout=30)
                    img_response.raise_for_status()
                    
                    # Temp dosyaya kaydet
                    fd, temp_path = tempfile.mkstemp(suffix=".png")
                    with os.fdopen(fd, 'wb') as f:
                        f.write(img_response.content)
                    
                    ops.info(f"Görsel indirildi: {temp_path}")
                    return temp_path
                    
                elif status_code == -1 or status_code > 1:
                    error_msg = poll_data.get('error', 'Bilinmeyen hata durumu')
                    ops.error(f"Kie AI Task Başarısız: {error_msg}")
                    raise Exception(f"Kie AI Task Failed: {error_msg}")
                
                ops.info(f"Bekleniyor... ({retry_count+1}/{max_retries})")
                retry_count += 1
                
            ops.error("Kie AI Zaman Aşımı", message="Görsel üretimi zaman aşımına uğradı")
            raise Exception("Kie AI polling zaman aşımı")

        except Exception as e:
            ops.error(f"Görsel üretme hatası: {e}", exception=e)
            raise
