from __future__ import annotations

"""
Production Pipeline — Video Üretim Orkestratörü
==================================================
Onaylanan senaryoyu alıp aşama aşama video üretir:

1. Nano Banana 2 → Giriş sahnesi görseli (first frame)
2. Seedance 2.0 → Video üretimi (image-to-video/text-to-video)
3. [Türkçe] ElevenLabs → Dış ses üretimi
4. [Türkçe] Replicate → Video + ses birleştirme
5. Notion loglama

Her aşamada progress callback ile Telegram'a bildirim gönderilir.
"""

import asyncio

from logger import get_logger

log = get_logger("production_pipeline")


class ProductionPipeline:
    """
    Video üretim orkestratörü.

    Tüm servisler dışarıdan enjekte edilir (Dependency Injection).
    Pipeline sadece akış kontrolüne odaklanır.
    """

    def __init__(
        self,
        kie_service,
        elevenlabs_service,
        replicate_service,
        notion_service,
        imgbb_service,
        is_dry_run: bool = False,
    ):
        self.kie = kie_service
        self.elevenlabs = elevenlabs_service
        self.replicate = replicate_service
        self.notion = notion_service
        self.imgbb = imgbb_service
        self.is_dry_run = is_dry_run

    async def produce(
        self,
        scenario: dict,
        collected_data: dict,
        progress_callback=None,
        user_name: str = "",
    ) -> dict:
        """
        Onaylanan senaryoyla video üretim pipeline'ını çalıştır.

        Args:
            scenario: ScenarioEngine çıktısı
            collected_data: Kullanıcıdan toplanan veriler
            progress_callback: async def callback(step: str, message: str)
                             Her aşamada Telegram'a bildirim göndermek için.
            user_name: Telegram kullanıcı adı

        Returns:
            dict: {
                "status": "success" | "failed",
                "video_url": str,           # Final video URL
                "first_frame_url": str,     # Üretilen giriş görseli
                "raw_video_url": str,       # Ses olmadan video
                "audio_url": str,           # Dış ses URL (varsa)
                "notion_page_url": str,     # Notion log URL
                "error": str,               # Hata mesajı (varsa)
                "cost": dict,               # Maliyet bilgisi
            }
        """
        brand = collected_data.get("brand_name", "?")
        product = collected_data.get("product_name", "?")
        concept = collected_data.get("ad_concept", "?")
        duration = scenario.get("duration", 10)
        aspect_ratio = scenario.get("aspect_ratio", "9:16")
        resolution = scenario.get("resolution", "720p")
        language = scenario.get("language", "Türkçe")
        cost = scenario.get("cost", {})
        product_image = collected_data.get("product_image")

        result = {
            "status": "failed",
            "video_url": "",
            "first_frame_url": "",
            "raw_video_url": "",
            "audio_url": "",
            "notion_page_url": "",
            "error": "",
            "cost": cost,
        }

        # ── DRY-RUN MODU ──
        if self.is_dry_run:
            log.info("🏜️ DRY-RUN: Pipeline simüle ediliyor")
            if progress_callback:
                await progress_callback("dry_run", "🏜️ DRY-RUN modu — gerçek API çağrısı yapılmıyor")
            result["status"] = "success"
            result["video_url"] = "https://example.com/dry-run-video.mp4"
            result["first_frame_url"] = "https://example.com/dry-run-frame.png"
            return result

        # ── NOTION LOG — "Üretiliyor" ──
        notion_page_url = None
        try:
            notion_page_url = await asyncio.to_thread(
                self.notion.log_production,
                brand=brand,
                product=product,
                concept=concept[:200],
                video_duration=duration,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                language=language,
                estimated_cost=cost.get("total_usd", 0),
                status="Üretiliyor",
                user_name=user_name,
            )
            result["notion_page_url"] = notion_page_url or ""
        except Exception:
            log.error("Notion log oluşturulamadı", exc_info=True)
            # Notion hatası pipeline'ı durdurmasın

        try:
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # ADIM 1: Giriş Görseli (Nano Banana 2)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            if progress_callback:
                await progress_callback("step_1", "🖼️ Giriş görseli üretiliyor (Nano Banana 2)...")

            image_prompt = scenario.get("image_prompt", "")
            first_frame_url = None

            if product_image:
                # Ürün fotoğrafı varsa — doğrudan kullan veya NB2 ile zenginleştir
                if image_prompt:
                    log.info("Nano Banana 2 ile giriş görseli üretiliyor...")
                    nb2_task = await asyncio.to_thread(
                        self.kie.create_image,
                        prompt=image_prompt,
                        aspect_ratio=aspect_ratio,
                        resolution="2k",
                        image_input=[product_image],
                    )
                    nb2_result = await asyncio.to_thread(self.kie.poll_task, nb2_task)

                    if nb2_result["status"] == "success" and nb2_result["urls"]:
                        first_frame_url = nb2_result["urls"][0]
                        log.info(f"NB2 giriş görseli hazır: {first_frame_url[:60]}...")
                    else:
                        log.warning("NB2 başarısız — ürün fotoğrafı doğrudan kullanılacak")
                        first_frame_url = product_image
                else:
                    first_frame_url = product_image
            else:
                # Ürün fotoğrafı yok — sıfırdan NB2 görsel üret
                if image_prompt:
                    nb2_task = await asyncio.to_thread(
                        self.kie.create_image,
                        prompt=image_prompt,
                        aspect_ratio=aspect_ratio,
                        resolution="2k",
                    )
                    nb2_result = await asyncio.to_thread(self.kie.poll_task, nb2_task)
                    if nb2_result["status"] == "success" and nb2_result["urls"]:
                        first_frame_url = nb2_result["urls"][0]

            result["first_frame_url"] = first_frame_url or ""

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # ADIM 2: Video Üretimi (Seedance 2.0)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            if progress_callback:
                await progress_callback("step_2", "🎬 Video üretiliyor (Seedance 2.0)... Bu 3-5 dakika sürebilir.")

            video_prompt = scenario.get("video_prompt", "")

            # Türkçe dış ses varsa, video'da konuşma olmamalı
            if language == "Türkçe" and "no dialogue" not in video_prompt.lower():
                video_prompt += " No dialogue, ambient sounds only."

            # Generate audio: İngilizce ise True, Türkçe ise False
            generate_audio = language != "Türkçe"

            video_task = await asyncio.to_thread(
                self.kie.create_video,
                prompt=video_prompt,
                duration=duration,
                resolution=resolution,
                aspect_ratio=aspect_ratio,
                generate_audio=generate_audio,
                first_frame_url=first_frame_url,
            )

            log.info(f"Seedance 2.0 video görevi: {video_task}")

            # Polling — event loop'u bloke etmemek için thread'de çalıştır
            video_result = await asyncio.to_thread(self.kie.poll_task, video_task)

            if video_result["status"] != "success" or not video_result.get("urls"):
                error_msg = video_result.get("error", "Video üretimi başarısız")
                raise RuntimeError(f"Seedance 2.0 hatası: {error_msg}")

            raw_video_url = video_result["urls"][0]
            result["raw_video_url"] = raw_video_url
            log.info(f"Video üretildi: {raw_video_url[:60]}...")

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # ADIM 3: Dış Ses (ElevenLabs) — Sadece Türkçe
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            final_video_url = raw_video_url  # Varsayılan: dış ses yok

            if language == "Türkçe":
                voiceover_text = scenario.get("voiceover_text", "")

                if voiceover_text:
                    if progress_callback:
                        await progress_callback(
                            "step_3",
                            "🎙️ Türkçe dış ses üretiliyor (ElevenLabs)..."
                        )

                    # Dış ses süre kontrolü — video süresini aşarsa metni kırp
                    from services.elevenlabs_service import ElevenLabsService
                    est_duration = ElevenLabsService.estimate_duration_seconds(voiceover_text)
                    if est_duration > duration + 2:  # 2 saniye tolerans
                        target_words = int(duration * 2.5)  # ~2.5 kelime/saniye
                        words = voiceover_text.split()
                        if len(words) > target_words:
                            voiceover_text = " ".join(words[:target_words])
                            log.warning(
                                f"Dış ses metni kırpıldı: {est_duration:.1f}s → ~{duration}s "
                                f"({len(words)} → {target_words} kelime)"
                            )

                    # ElevenLabs TTS
                    log.info(f"ElevenLabs TTS başlıyor: {len(voiceover_text)} karakter")
                    audio_bytes = await asyncio.to_thread(
                        self.elevenlabs.generate_speech,
                        text=voiceover_text,
                        voice_name="Sarah",
                        stability=0.5,
                        similarity_boost=0.75,
                        style=0.4,
                    )

                    # Ses dosyasını hosting'e yükle (Replicate erişebilsin)
                    audio_url = await asyncio.to_thread(
                        self.elevenlabs.upload_audio_to_hosting,
                        audio_bytes,
                    )
                    result["audio_url"] = audio_url
                    log.info(f"Dış ses hazır: {audio_url[:60]}...")

                    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    # ADIM 4: Video + Ses Birleştirme (Replicate)
                    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    if progress_callback:
                        await progress_callback(
                            "step_4",
                            "🔀 Video ve dış ses birleştiriliyor (Replicate)..."
                        )

                    final_video_url = await asyncio.to_thread(
                        self.replicate.merge_video_audio,
                        video_url=raw_video_url,
                        audio_url=audio_url,
                        replace_audio=False,
                    )
                    log.info(f"Video+ses birleştirildi: {final_video_url[:60]}...")
                else:
                    log.warning("Dış ses metni boş — ses eklenmeden devam ediliyor")
            else:
                log.info("Dil İngilizce — Seedance native ses kullanılıyor, ek işlem yok")

            result["video_url"] = final_video_url
            result["status"] = "success"

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # ADIM 5: Notion güncelle — "Tamamlandı"
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            if notion_page_url:
                # Notion page ID'yi URL'den çıkar
                page_id = self._extract_page_id(notion_page_url)
                if page_id:
                    await asyncio.to_thread(
                        self.notion.update_production_status,
                        page_id=page_id,
                        status="Tamamlandı",
                        video_url=final_video_url,
                    )

            if progress_callback:
                await progress_callback("complete", "✅ Video başarıyla üretildi!")

            log.info(
                f"Pipeline tamamlandı: {brand} — {product} | "
                f"video={final_video_url[:50]}... | cost=${cost.get('total_usd', 0):.3f}"
            )

        except Exception as e:
            error_msg = str(e)[:500]
            result["error"] = error_msg
            log.error(f"Pipeline hatası: {error_msg}", exc_info=True)

            # Notion güncelle — "Hata"
            if notion_page_url:
                page_id = self._extract_page_id(notion_page_url)
                if page_id:
                    await asyncio.to_thread(
                        self.notion.update_production_status,
                        page_id=page_id,
                        status="Hata",
                        error_message=error_msg,
                    )

            if progress_callback:
                await progress_callback("error", f"❌ Üretim hatası: {error_msg[:200]}")

        return result

    # ── YARDIMCI ──

    @staticmethod
    def _extract_page_id(notion_url: str) -> str | None:
        """Notion page URL'inden page ID çıkar."""
        if not notion_url:
            return None
        try:
            # URL formatı: https://www.notion.so/Title-abc123def456...
            # Son 32 karakter (tire olmadan) page ID
            clean = notion_url.rstrip("/").split("?")[0]
            last_part = clean.split("-")[-1] if "-" in clean else clean.split("/")[-1]

            # 32 hex karakter → UUID formatına çevir
            if len(last_part) == 32:
                return (
                    f"{last_part[:8]}-{last_part[8:12]}-{last_part[12:16]}-"
                    f"{last_part[16:20]}-{last_part[20:]}"
                )
            return last_part
        except Exception:
            return None
