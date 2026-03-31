"""
Notion Loglama Servisi
Analiz sonuçlarını Notion database'e yazar.
"""

import json
from datetime import datetime, timezone

import requests

from logger import get_logger

log = get_logger("notion_logger")


class NotionLogger:
    """Supplement analiz sonuçlarını Notion'a loglar."""

    BASE_URL = "https://api.notion.com/v1"

    def __init__(self, token: str, database_id: str):
        self.token = token
        self.database_id = database_id
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }

    def log_analysis(self, analysis_result: dict, model: str, success: bool) -> str | None:
        """
        Analiz sonucunu Notion database'e yaz.

        Returns:
            str: Oluşturulan Notion page URL'i veya None (hata durumunda)
        """
        parsed = analysis_result.get("parsed") or {}
        urun = parsed.get("urun_bilgisi", {})
        kullanim = parsed.get("kullanim_onerisi", {})
        diger = parsed.get("diger_bilgiler", {})
        icerik_tablosu = parsed.get("icerik_tablosu", [])

        urun_adi = urun.get("urun_adi", "Bilinmeyen Ürün")
        marka = urun.get("marka", "")
        urun_turu = urun.get("urun_turu", "")
        porsiyon = urun.get("porsiyon_buyuklugu", "")
        toplam_porsiyon = urun.get("toplam_porsiyon", "")
        bilesim = parsed.get("bilesim", "")
        kullanim_str = kullanim.get("onerilen_kullanim", "")
        if kullanim.get("gunluk_doz"):
            kullanim_str += f" | Doz: {kullanim['gunluk_doz']}"
        saklama = diger.get("saklama_kosullari", "")
        icerik_sayisi = len(icerik_tablosu)

        # Durum
        if success and icerik_sayisi > 0:
            durum = "✅ Başarılı"
        elif success:
            durum = "⚠️ Kısmi"
        else:
            durum = "❌ Başarısız"

        # Tür select mapping
        tur_map = {
            "tablet": "Tablet",
            "kapsül": "Kapsül",
            "kapsul": "Kapsül",
            "toz": "Toz",
            "likit": "Likit",
            "sıvı": "Likit",
            "softjel": "Softjel",
            "soft gel": "Softjel",
        }
        tur_select = tur_map.get(urun_turu.lower().strip(), "Diğer") if urun_turu else "Diğer"

        # ── İçerik tablosu Notion table blokları ──
        table_children = self._build_content_table(icerik_tablosu)

        # ── Notion page payload ──
        payload = {
            "parent": {"database_id": self.database_id},
            "properties": {
                "Ürün Adı": {"title": [{"text": {"content": _truncate(urun_adi, 100)}}]},
                "Marka": {"rich_text": [{"text": {"content": _truncate(marka, 100)}}]},
                "Tür": {"select": {"name": tur_select}},
                "İçerik Sayısı": {"number": icerik_sayisi},
                "Porsiyon": {"rich_text": [{"text": {"content": _truncate(porsiyon, 100)}}]},
                "Toplam Porsiyon": {"rich_text": [{"text": {"content": _truncate(str(toplam_porsiyon), 100)}}]},
                "Bileşim": {"rich_text": [{"text": {"content": _truncate(bilesim, 2000)}}]},
                "Kullanım Önerisi": {"rich_text": [{"text": {"content": _truncate(kullanim_str, 500)}}]},
                "Saklama Koşulları": {"rich_text": [{"text": {"content": _truncate(saklama, 200)}}]},
                "Model": {"select": {"name": model}},
                "Durum": {"select": {"name": durum}},
                "Analiz Tarihi": {"date": {"start": datetime.now(timezone.utc).strftime("%Y-%m-%d")}},
            },
            "children": table_children,
        }

        try:
            resp = requests.post(
                f"{self.BASE_URL}/pages",
                headers=self.headers,
                json=payload,
                timeout=30,
            )

            if resp.status_code == 200:
                page_url = resp.json().get("url", "")
                log.info(f"Notion'a yazıldı: {urun_adi} → {page_url}")
                return page_url
            else:
                log.error(f"Notion API hatası ({resp.status_code}): {resp.text[:500]}")
                return None

        except Exception:
            log.error("Notion'a yazma hatası", exc_info=True)
            return None

    def _build_content_table(self, icerik_tablosu: list) -> list:
        """İçerik tablosunu Notion table bloğuna dönüştür."""
        if not icerik_tablosu:
            return [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": "İçerik tablosu çıkarılamadı."}}]
                    },
                }
            ]

        # Header
        header_row = {
            "type": "table_row",
            "table_row": {
                "cells": [
                    [{"type": "text", "text": {"content": "Madde"}}],
                    [{"type": "text", "text": {"content": "Miktar"}}],
                    [{"type": "text", "text": {"content": "%BRD"}}],
                ]
            },
        }

        # Data rows (max 98 — Notion limit 100 blocks)
        data_rows = []
        for item in icerik_tablosu[:98]:
            madde = item.get("madde_adi", "")
            miktar = item.get("miktar", "")
            birim = item.get("birim", "")
            brd = item.get("brd_yuzde", "")

            miktar_str = f"{miktar} {birim}".strip() if birim else str(miktar)

            data_rows.append({
                "type": "table_row",
                "table_row": {
                    "cells": [
                        [{"type": "text", "text": {"content": str(madde)}}],
                        [{"type": "text", "text": {"content": str(miktar_str)}}],
                        [{"type": "text", "text": {"content": str(brd)}}],
                    ]
                },
            })

        children = [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "📊 İçerik Tablosu"}}]
                },
            },
            {
                "object": "block",
                "type": "table",
                "table": {
                    "table_width": 3,
                    "has_column_header": True,
                    "has_row_header": False,
                    "children": [header_row] + data_rows,
                },
            },
        ]

        return children


def _truncate(text: str, max_len: int) -> str:
    """Notion rich_text karakter limitlerine uygun kısaltma."""
    if not text:
        return ""
    text = str(text)
    return text[:max_len] if len(text) > max_len else text
