from __future__ import annotations

"""
Production Pipeline — Deterministik Video Üretim Orkestratörü
===============================================================
Onaylanan senaryoyu alıp 4 adımda video üretir:

1. Seedance 2.0 → Video üretimi (reference image modu)
2. ElevenLabs → Türkçe dış ses üretimi
3. Replicate → Video + ses birleştirme
4. Notion loglama

Deterministik kurallar:
- 10 saniye, 9:16, 720p (sabit)
- Reference image: ürün görselleri reference_image_urls olarak verilir
- Karakter konuşması YOK — ambient sesler AÇIK
- Dış ses her zaman Türkçe, ~25 kelime, ElevenLabs
- Birleştirme: replace_audio=False (ambient + dış ses overlay)

Her aşamada progress callback ile Telegram'a bildirim gönderilir.
"""

import asyncio

from logger import get_logger

log = get_logger("production_pipeline")


class ProductionPipeline:
    """
    Deterministik video üretim orkestratörü.

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
        preferences: dict = None,
    ) -> dict:
        """
        Onaylanan senaryoyla deterministik video üretim pipeline'ını çalıştır.

        Args:
            scenario: ScenarioEngine çıktısı
            collected_data: URLDataExtractor'dan gelen veriler
            progress_callback: async def callback(step: str, message: str)
                             Her aşamada Telegram'a bildirim göndermek için.
            user_name: Telegram kullanıcı adı
            preferences: Kullanıcı tercihleri

        Returns:
            dict: {
                "status": "success" | "failed",
                "video_url": str,           # Final video URL
                "raw_video_url": str,       # Ses olmadan video
                "audio_url": str,           # Dış ses URL
                "notion_page_url": str,     # Notion log URL
                "error": str,               # Hata mesajı (varsa)
                "cost": dict,               # Maliyet bilgisi
            }
        """
        brand = collected_data.get("brand_name", "?")
        product = collected_data.get("product_name", "?")
        concept = collected_data.get("ad_concept", "?")
        duration = scenario.get("duration", 10)
        
        preferences = preferences or {}
        raw_aspect = str(preferences.get("video_format") or scenario.get("aspect_ratio", "9:16"))
        
        # Merkezi normalizasyon (kie_api.py'deki tek kaynak)
        from services.kie_api import normalize_aspect_ratio
        aspect_ratio = normalize_aspect_ratio(raw_aspect)
        log.info(f"Aspect ratio: '{raw_aspect}' → '{aspect_ratio}'")

        language = scenario.get("language", "Türkçe")
        cost = scenario.get("cost", {})
        reference_images = collected_data.get("best_image_urls", [])

        result = {
            "status": "failed",
            "video_url": "",
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
            return result

        # ── KIE AI KREDİ BAKİYE KONTROLÜ ──
        try:
            credit_data = await asyncio.to_thread(self.kie.get_credit_balance)
            credit_balance = 0.0
            if credit_data and isinstance(credit_data, dict):
                data_block = credit_data.get("data", credit_data)
                if isinstance(data_block, dict):
                    credit_balance = float(data_block.get("balance", data_block.get("credit", 0)))
                else:
                    try:
                        credit_balance = float(data_block)
                    except (ValueError, TypeError):
                        pass
            MIN_CREDIT_THRESHOLD = 0.50
            if 0 < credit_balance < MIN_CREDIT_THRESHOLD:
                error_msg = (
                    f"Kie AI kredi bakiyesi yetersiz: ${credit_balance:.2f} "
                    f"(minimum ${MIN_CREDIT_THRESHOLD:.2f} gerekli)"
                )
                log.error(error_msg)
                result["error"] = error_msg
                if progress_callback:
                    await progress_callback("credit_error", f"💰 {error_msg}")
                return result
            if credit_balance > 0:
                log.info(f"Kie AI kredi bakiyesi: ${credit_balance:.2f} — yeterli")
        except Exception:
            log.warning("Kie AI kredi bakiyesi sorgulanamadı — pipeline devam ediyor", exc_info=True)

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
                resolution="720p",
                language=language,
                estimated_cost=cost.get("total_usd", 0),
                status="Üretiliyor",
                user_name=user_name,
            )
            result["notion_page_url"] = notion_page_url or ""
            if isinstance(notion_page_url, str) and notion_page_url:
                result["_notion_page_id"] = self._extract_page_id(notion_page_url)
        except Exception:
            log.error("Notion log oluşturulamadı", exc_info=True)

        try:
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # ADIM 1: Video Üretimi (Seedance 2.0 — Reference Image)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            if progress_callback:
                ref_count = len(reference_images) if reference_images else 0
                await progress_callback(
                    "step_1",
                    f"🎬 Video üretiliyor (Seedance 2.0, {ref_count} referans görsel)... "
                    f"Bu 3-5 dakika sürebilir."
                )

            video_prompt = scenario.get("video_prompt", "")

            # Güvenlik: Konuşma yasağını prompt'a zorla ekle
            no_dialogue_clause = "No character dialogue, no speaking, no lip movement. Enable ambient and environmental sounds, natural atmosphere."
            if "no dialogue" not in video_prompt.lower() and "no speaking" not in video_prompt.lower():
                video_prompt += f" {no_dialogue_clause}"

            video_task = await asyncio.to_thread(
                self.kie.create_video,
                prompt=video_prompt,
                duration=duration,
                aspect_ratio=aspect_ratio,
                generate_audio=True,  # Ambient sesler AÇIK
                reference_images=reference_images if reference_images else None,
            )

            log.info(f"Seedance 2.0 video görevi: {video_task}")

            # Async polling — event loop'u bloke etmez
            video_result = await self.kie.async_poll_task(video_task)

            if video_result["status"] != "success" or not video_result.get("urls"):
                error_msg = video_result.get("error", "Video üretimi başarısız")
                
                # Safety filter — prompt rewrite ile tekrar dene
                if any(keyword in error_msg.lower() for keyword in ["safety", "sensitive", "content policy", "nsfw"]):
                    log.warning(f"Safety filter tetiklendi: {error_msg[:100]}. Prompt yeniden yazılıyor...")
                    if progress_callback:
                        await progress_callback("retry_safety", "⚠️ Güvenlik filtresi tetiklendi — prompt yeniden yazılıyor...")
                    
                    try:
                        rewritten_prompt = await self._rewrite_prompt_for_safety(video_prompt)
                        if rewritten_prompt and rewritten_prompt != video_prompt:
                            log.info(f"Prompt yeniden yazıldı: {len(video_prompt)} -> {len(rewritten_prompt)} karakter")
                            video_task2 = await asyncio.to_thread(
                                self.kie.create_video,
                                prompt=rewritten_prompt,
                                duration=duration,
                                aspect_ratio=aspect_ratio,
                                generate_audio=True,
                                reference_images=reference_images if reference_images else None,
                            )
                            video_result2 = await self.kie.async_poll_task(video_task2)
                            if video_result2["status"] == "success" and video_result2.get("urls"):
                                raw_video_url = video_result2["urls"][0]
                                result["raw_video_url"] = raw_video_url
                                log.info(f"Safety rewrite başarılı: {raw_video_url[:60]}...")
                            else:
                                raise RuntimeError(f"Seedance 2.0 safety rewrite de başarısız: {video_result2.get('error', '?')}")
                        else:
                            raise RuntimeError(f"Seedance 2.0 hatası: {error_msg}")
                    except RuntimeError:
                        raise
                    except Exception as rewrite_err:
                        log.error(f"Prompt rewrite hatası: {rewrite_err}", exc_info=True)
                        raise RuntimeError(f"Seedance 2.0 hatası (safety): {error_msg}")
                else:
                    raise RuntimeError(f"Seedance 2.0 hatası: {error_msg}")
            else:
                raw_video_url = video_result["urls"][0]
                result["raw_video_url"] = raw_video_url

            log.info(f"Video üretildi: {raw_video_url[:60]}...")

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # ADIM 2: Türkçe Dış Ses (ElevenLabs)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            voiceover_text = scenario.get("voiceover_text", "")

            if voiceover_text:
                # ── Graceful Degradation: Dış ses başarısız olursa video yine teslim edilir ──
                voiceover_succeeded = False
                try:
                    if progress_callback:
                        await progress_callback(
                            "step_2",
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

                    # Ses dosyasını hosting'e yükle
                    audio_url = await asyncio.to_thread(
                        self.elevenlabs.upload_audio_to_hosting,
                        audio_bytes,
                        imgbb_api_key=self.imgbb.api_key,
                    )
                    result["audio_url"] = audio_url
                    log.info(f"Dış ses hazır: {audio_url[:60]}...")

                    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    # ADIM 3: Video + Ses Birleştirme (Replicate)
                    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    if progress_callback:
                        await progress_callback(
                            "step_3",
                            "🔀 Video ve dış ses birleştiriliyor (Replicate)..."
                        )

                    # Async merge — ambient ses korunur + dış ses overlay
                    final_video_url = await self.replicate.async_merge_video_audio(
                        video_url=raw_video_url,
                        audio_url=audio_url,
                        replace_audio=False,  # Ambient sesler + Türkçe dış ses
                    )
                    log.info(f"Video+ses birleştirildi: {final_video_url[:60]}...")
                    voiceover_succeeded = True

                except Exception as vo_err:
                    # ── GRACEFUL DEGRADATION ──
                    # Dış ses veya birleştirme başarısız → ambient-only video teslim edilir
                    log.error(
                        f"Dış ses/birleştirme hatası (graceful degradation): {vo_err}",
                        exc_info=True,
                    )
                    final_video_url = raw_video_url
                    result["voiceover_error"] = str(vo_err)[:300]
                    if progress_callback:
                        await progress_callback(
                            "voiceover_warning",
                            "⚠️ Dış ses eklenemedi — video ambient seslerle teslim edilecek."
                        )
            else:
                log.warning("Dış ses metni boş — ses eklenmeden devam ediliyor")
                final_video_url = raw_video_url

            result["video_url"] = final_video_url
            result["status"] = "success"

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # ADIM 4: Notion güncelle — "Tamamlandı"
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            if notion_page_url:
                page_id = result.get("_notion_page_id") or self._extract_page_id(notion_page_url)
                if page_id:
                    try:
                        await asyncio.to_thread(
                            self.notion.update_production_status,
                            page_id=page_id,
                            status="Tamamlandı",
                            video_url=final_video_url,
                        )
                    except Exception:
                        log.error("Notion 'Tamamlandı' güncellemesi başarısız", exc_info=True)

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

            if notion_page_url:
                page_id = result.get("_notion_page_id") or self._extract_page_id(notion_page_url)
                if page_id:
                    try:
                        await asyncio.to_thread(
                            self.notion.update_production_status,
                            page_id=page_id,
                            status="Hata",
                            error_message=error_msg,
                        )
                    except Exception:
                        log.error("Notion 'Hata' güncellemesi başarısız", exc_info=True)

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
            clean = notion_url.rstrip("/").split("?")[0]
            last_part = clean.split("-")[-1] if "-" in clean else clean.split("/")[-1]
            if len(last_part) == 32:
                return (
                    f"{last_part[:8]}-{last_part[8:12]}-{last_part[12:16]}-"
                    f"{last_part[16:20]}-{last_part[20:]}"
                )
            return last_part
        except Exception:
            return None

    @staticmethod
    async def _rewrite_prompt_for_safety(original_prompt: str) -> str:
        """
        Safety filter'a takılan prompt'u daha güvenli hale yeniden yazar.
        GPT-4.1 Mini kullanır.
        """
        import openai
        import os
        try:
            client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a prompt rewriting assistant. The following video generation prompt "
                            "was rejected by a content safety filter. Rewrite it to be safe while "
                            "preserving the creative intent. Remove any potentially sensitive "
                            "references to human bodies, violence, or controversial topics. "
                            "Focus on product features, aesthetics, and cinematic quality. "
                            "Return ONLY the rewritten prompt, nothing else."
                        ),
                    },
                    {"role": "user", "content": f"Original prompt:\n{original_prompt}"},
                ],
                max_completion_tokens=800,
            )
            rewritten = response.choices[0].message.content or ""
            return rewritten.strip()
        except Exception as e:
            from logger import get_logger
            get_logger("production_pipeline").error(f"Prompt rewrite hatası: {e}", exc_info=True)
            return ""
