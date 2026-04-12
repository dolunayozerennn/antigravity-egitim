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

        # ── KIE AI KREDİ BAKİYE KONTROLÜ ──
        try:
            credit_data = await asyncio.to_thread(self.kie.get_credit_balance)
            credit_balance = 0.0
            if credit_data and isinstance(credit_data, dict):
                # API yapısına göre bakiyeyi çek
                data_block = credit_data.get("data", credit_data)
                credit_balance = float(
                    data_block.get("balance", data_block.get("credit", 0))
                )
            MIN_CREDIT_THRESHOLD = 0.50  # Minimum $0.50 bakiye gerekli
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
            # Kredi sorgulama hatası pipeline'ı durdurmasın — devam et
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
                resolution=resolution,
                language=language,
                estimated_cost=cost.get("total_usd", 0),
                status="Üretiliyor",
                user_name=user_name,
            )
            result["notion_page_url"] = notion_page_url or ""
            # Page ID'yi doğrudan sakla (Önerildi: URL parse'dan daha güvenilir)
            if isinstance(notion_page_url, str) and notion_page_url:
                result["_notion_page_id"] = self._extract_page_id(notion_page_url)
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
                    try:
                        nb2_task = await asyncio.to_thread(
                            self.kie.create_image,
                            prompt=image_prompt,
                            aspect_ratio=aspect_ratio,
                            resolution="2k",
                            image_input=[product_image],
                        )
                        nb2_result = await self.kie.async_poll_task(nb2_task)

                        if nb2_result["status"] == "success" and nb2_result["urls"]:
                            first_frame_url = nb2_result["urls"][0]
                            log.info(f"NB2 giriş görseli hazır: {first_frame_url[:60]}...")
                        else:
                            log.warning("NB2 başarısız — ürün fotoğrafı doğrudan kullanılacak")
                            first_frame_url = product_image
                    except Exception as e:
                        log.warning(f"NB2 görsel üretim hatası — fallback: product_image: {e}")
                        first_frame_url = product_image
                else:
                    first_frame_url = product_image
            else:
                # Ürün fotoğrafı yok — sıfırdan NB2 görsel üret
                if image_prompt:
                    try:
                        nb2_task = await asyncio.to_thread(
                            self.kie.create_image,
                            prompt=image_prompt,
                            aspect_ratio=aspect_ratio,
                            resolution="2k",
                        )
                        nb2_result = await self.kie.async_poll_task(nb2_task)
                        if nb2_result["status"] == "success" and nb2_result["urls"]:
                            first_frame_url = nb2_result["urls"][0]
                        else:
                            log.warning("NB2 text-to-image başarısız — first_frame olmadan devam ediliyor")
                    except Exception as e:
                        log.warning(f"NB2 text-to-image hatası — first_frame olmadan devam: {e}")

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

            # Async polling — event loop'u bloke etmez
            video_result = await self.kie.async_poll_task(video_task)

            if video_result["status"] != "success" or not video_result.get("urls"):
                error_msg = video_result.get("error", "Video üretimi başarısız")
                
                # P1-4: Safety filter — prompt rewrite ile tekrar dene
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
                                resolution=resolution,
                                aspect_ratio=aspect_ratio,
                                generate_audio=generate_audio,
                                first_frame_url=first_frame_url,
                            )
                            video_result2 = await self.kie.async_poll_task(video_task2)
                            if video_result2["status"] == "success" and video_result2.get("urls"):
                                raw_video_url = video_result2["urls"][0]
                                result["raw_video_url"] = raw_video_url
                                log.info(f"Safety rewrite başarılı: {raw_video_url[:60]}...")
                                # Normal akışa devam — aşağıdaki adımlara geç
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

                    # Ses dosyasını hosting'e yükle (ImgBB birincil, tmpfiles yedek)
                    audio_url = await asyncio.to_thread(
                        self.elevenlabs.upload_audio_to_hosting,
                        audio_bytes,
                        imgbb_api_key=self.imgbb.api_key,
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

                    # Async merge — event loop'u bloke etmez
                    final_video_url = await self.replicate.async_merge_video_audio(
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
