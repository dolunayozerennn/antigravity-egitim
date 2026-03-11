from pydantic import BaseModel, Field
from typing import List, Optional

class SequenceConfig(BaseModel):
    toplam_adim: int = 3
    bekleme_suresi_acilmadi: int = 4
    bekleme_suresi_cevaplanmadi: int = 3
    gunluk_gonderim_limiti: int = 30
    gonderim_araligi: int = 5
    gonderim_saatleri: str = "09:00-17:00"
    gonderim_gunleri: str = "Pazartesi-Cuma"
    saat_dilimi: str = "UTC+3"

class Campaign(BaseModel):
    kampanya_id: str
    ad: str
    aciklama: str
    hedef_sektor: str
    icp_tanimi: dict = Field(default_factory=dict)
    deger_onerisi: str
    ilham_mailleri_paths: List[str] = Field(default_factory=list)
    sequence_kurallari: SequenceConfig = Field(default_factory=SequenceConfig)
    dil: str = "TR"
    hedef_metrikler: dict = Field(default_factory=lambda: {
        "open_rate_target": 0.40,
        "reply_rate_target": 0.10,
        "meeting_rate_target": 0.03
    })
