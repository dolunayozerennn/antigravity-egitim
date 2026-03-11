from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class EnrichmentData(BaseModel):
    teknoloji_stacki: List[str] = Field(default_factory=list)
    son_haberler: List[str] = Field(default_factory=list)
    funding_bilgisi: str = ""
    buyume_sinyalleri: List[str] = Field(default_factory=list)

class SequenceStatus(BaseModel):
    mevcut_adim: int = 1
    son_gonderim_tarihi: Optional[str] = None
    mail_acildi: bool = False
    mail_cevaplandi: bool = False
    cevap_tipi: Literal["olumlu", "olumsuz", "soru", "ooo", "bounce", "yok"] = "yok"
    sonraki_aksiyon_tarihi: Optional[str] = None

class Lead(BaseModel):
    lead_id: str
    ad: str
    soyad: str
    email: str
    email_dogrulama_durumu: Literal["deliverable", "risky", "undeliverable", "unknown"] = "unknown"
    sirket: str
    pozisyon: str
    sektor: Optional[str] = ""
    sirket_buyuklugu: Optional[str] = ""
    website: Optional[str] = ""
    linkedin: Optional[str] = ""
    ulke: Optional[str] = ""
    sehir: Optional[str] = ""
    enrichment: EnrichmentData = Field(default_factory=EnrichmentData)
    kampanya_id: str
    sequence_durumu: SequenceStatus = Field(default_factory=SequenceStatus)
