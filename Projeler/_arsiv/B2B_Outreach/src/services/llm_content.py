import os
import openai
from typing import Dict, Any, List
from src.models.lead import Lead
from src.models.campaign import Campaign

class LLMEmailGenerator:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        openai.api_key = self.api_key
        self.model = "gpt-4o"

    def generate_email(self, lead: Lead, campaign: Campaign, template_content: str) -> Dict[str, str]:
        system_prompt = (
            "Sen bir B2B Cold Email Content Specialist'sin. Amacın, sana verilen email şablonunu "
            "hedef kitle ve lead verilerine göre en iyi şekilde kişiselleştirmek. E-posta, "
            "'elle yazılmış', doğal, samimi bir dille olmalı, pazarlama veya satış dili olmamalı. "
            "Aşağıdaki değişkenleri dinamik ve doğal bir bağlamda doldurmalısın.\n"
            "- {ad}: Alıcının adı\n"
            "- {sirket}: Şirketin adı\n"
            "- {pozisyon}: Alıcının pozisyonu\n"
            "- {sektor_pain_point}: Sektöre özel acı nokta\n"
            "- {deger_onerisi}: Kampanyanın değer önerisi\n"
            "- {kanca}: Kişiye/şirkete özel dikkat çekici açılış (son haberler, teknoloji stacki veya LinkedIn profili)\n"
            "- {cta}: Eylem çağrısı"
        )
        
        user_prompt = f"""
Lütfen aşağıdaki şablona uygun, kişiselleştirilmiş bir soğuk e-posta (subject ve body) üret. 
Çıktıyı 'Subject:' ve 'Body:' olarak belirgin şekilde ve belirlenen dilde ({campaign.dil}) döndür.

----- Lead Bilgileri -----
Ad Soyad: {lead.ad} {lead.soyad}
Şirket: {lead.sirket}
Pozisyon: {lead.pozisyon}
Sektör: {lead.sektor}
Teknoloji Stacki: {lead.enrichment.teknoloji_stacki}
Son Haberler: {lead.enrichment.son_haberler}
Buyume: {lead.enrichment.buyume_sinyalleri}

----- Kampanya Bilgileri -----
Hedef Sektör: {campaign.hedef_sektor}
Değer Önerisi: {campaign.deger_onerisi}

----- Email Şablonu -----
{template_content}
"""

        try:
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=600
            )
            
            content = response.choices[0].message.content.strip()
            return self._parse_llm_output(content)
            
        except Exception as e:
            print(f"LLM e-posta üretimi hatası: {e}")
            return {"subject": "", "body": ""}

    def _parse_llm_output(self, content: str) -> Dict[str, str]:
        # A simple parser assuming the output is separated by 'Subject:' and 'Body:'
        subject = ""
        body = content
        
        if "Subject:" in content and "Body:" in content:
            parts = content.split("Body:", 1)
            subject_part = parts[0].split("Subject:", 1)
            if len(subject_part) > 1:
                subject = subject_part[1].strip()
            body = parts[1].strip()
            
        return {"subject": subject.strip("*'\""), "body": body.strip()}
