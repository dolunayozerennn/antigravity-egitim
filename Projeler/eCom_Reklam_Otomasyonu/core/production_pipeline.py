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
            # ADIM 0: ÖNCE VOICEOVER ÜRET → SÜRE ÖLÇ → VIDEO DURATION'I AYARLA
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # WHY: Önceki akışta video üretilip voiceover sonra geldiğinden,
            # ses video'dan kısa kalıp 7-9s sessiz boşluk doğuyordu. Şimdi
            # ses gerçek süresine göre video duration'ı round'lanıyor.
            voiceover_text = scenario.get("voiceover_text", "") or ""

            # Türkçe sayı/yüzde/birim normalizasyonu — LLM "%10" yazsa bile düzelt
            if voiceover_text:
                from utils.text_normalizer import normalize_for_tts
                normalized = normalize_for_tts(voiceover_text)
                if normalized != voiceover_text:
                    log.info(
                        f"Voiceover normalize edildi: rakam/birim Türkçe yazıya çevrildi"
                    )
                    voiceover_text = normalized

            audio_bytes = None
            audio_url = ""
            audio_duration = 0.0
            voiceover_succeeded = True  # boş voiceover veya başarılı = True

            if voiceover_text:
                voiceover_succeeded = False
                try:
                    if progress_callback:
                        await progress_callback(
                            "step_voiceover",
                            "🎙️ Türkçe dış ses üretiliyor (ElevenLabs v3)..."
                        )
                    log.info(f"ElevenLabs TTS başlıyor: {len(voiceover_text)} karakter")
                    audio_bytes = await asyncio.to_thread(
                        self.elevenlabs.generate_speech,
                        text=voiceover_text,
                        voice_name="Sarah",
                    )
                    from services.elevenlabs_service import ElevenLabsService
                    audio_duration = ElevenLabsService.measure_audio_duration(audio_bytes)
                    log.info(f"Voiceover gerçek süresi: {audio_duration:.2f}s")

                    # Replicate storage'a yükle (merge için URL lazım)
                    audio_url = await self.replicate.async_upload_audio(audio_bytes)
                    result["audio_url"] = audio_url
                    log.info(f"Dış ses Replicate storage'a yüklendi: {audio_url[:80]}...")
                    voiceover_succeeded = True
                except Exception as vo_err:
                    log.error(
                        f"Dış ses üretim hatası (graceful degradation): {vo_err}",
                        exc_info=True,
                    )
                    result["voiceover_error"] = str(vo_err)[:300]
                    if progress_callback:
                        await progress_callback(
                            "voiceover_warning",
                            "⚠️ Dış ses üretilemedi — video ambient seslerle teslim edilecek."
                        )

            # Video duration'ı ses süresine göre round et (Seedance 5/10/15)
            def _round_to_seedance_duration(audio_sec: float) -> int:
                if audio_sec <= 7:
                    return 5
                elif audio_sec <= 12:
                    return 10
                elif audio_sec <= 15:
                    return 15
                else:
                    # >15s: multi-scene'e bırak — caller >15 olduğunda multi'ye girer
                    return 15

            if audio_duration > 0:
                new_duration = _round_to_seedance_duration(audio_duration)
                if new_duration != duration:
                    log.info(
                        f"Video duration ses süresine göre güncellendi: "
                        f"{duration}s → {new_duration}s (ses {audio_duration:.1f}s)"
                    )
                duration = new_duration

            # Multi-scene koruyucu: scene_count>1 ama final duration ≤15 ise tek sahneye düşür
            is_multi = bool(scenario.get("is_multi_scene")) and duration > 15
            if scenario.get("is_multi_scene") and not is_multi:
                scenes_list = scenario.get("scenes") or []
                if scenes_list:
                    log.warning(
                        f"Multi-scene senaryo {duration}s için tek sahneye düşürüldü "
                        f"(tutarlılık için 1 sahne tercih edildi)"
                    )
                    scenario["is_multi_scene"] = False
                    scenario["scene_count"] = 1
                    scenario["scenes"] = [scenes_list[0]]

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # ADIM 1: VIDEO ÜRETİMİ
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            if scenario.get("is_multi_scene") and duration > 15:
                raw_video_url = await self._produce_multi_scene(
                    scenario=scenario,
                    reference_images=reference_images,
                    duration=duration,
                    aspect_ratio=aspect_ratio,
                    progress_callback=progress_callback,
                )
                result["raw_video_url"] = raw_video_url
                log.info(f"Multi-scene video üretildi: {raw_video_url[:60]}...")
            else:
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                # ADIM 1: Video Üretimi (Seedance 2.0 — Reference Image) [TEK SAHNE]
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                if progress_callback:
                    ref_count = len(reference_images) if reference_images else 0
                    await progress_callback(
                        "step_1",
                        f"🎬 Video üretiliyor (Seedance 2.0, {duration}s, {ref_count} referans görsel)... "
                        f"Bu 3-5 dakika sürebilir."
                    )

                # scenes[0].video_prompt öncelikli, yoksa eski video_prompt key'i
                scenes_list = scenario.get("scenes") or []
                if scenes_list and scenes_list[0].get("video_prompt"):
                    video_prompt = scenes_list[0]["video_prompt"]
                else:
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
                    generate_audio=True,
                    reference_images=reference_images if reference_images else None,
                )

                log.info(f"Seedance 2.0 video görevi: {video_task}")

                # Async polling — event loop'u bloke etmez
                video_result = await self.kie.async_poll_task(video_task)

                if video_result["status"] != "success" or not video_result.get("urls"):
                    error_msg = video_result.get("error", "Video üretimi başarısız")

                    # Reference image format hatası → text-to-video fallback
                    if reference_images and "image format" in error_msg.lower():
                        log.warning(f"Single-scene ref_image reddedildi → text-to-video fallback: {error_msg}")
                        if progress_callback:
                            await progress_callback("retry_no_ref", "⚠️ Ürün görseli desteklenmiyor — referans görsel olmadan tekrar deneniyor...")
                        video_task_fallback = await asyncio.to_thread(
                            self.kie.create_video,
                            prompt=video_prompt,
                            duration=duration,
                            aspect_ratio=aspect_ratio,
                            generate_audio=True,
                            reference_images=None,
                        )
                        video_result_fallback = await self.kie.async_poll_task(video_task_fallback)
                        if video_result_fallback["status"] == "success" and video_result_fallback.get("urls"):
                            raw_video_url = video_result_fallback["urls"][0]
                            result["raw_video_url"] = raw_video_url
                            log.info(f"Text-to-video fallback başarılı: {raw_video_url[:60]}...")
                        else:
                            raise RuntimeError(f"Seedance 2.0 fallback de başarısız: {video_result_fallback.get('error', '?')}")

                    # Safety filter — prompt rewrite ile tekrar dene
                    elif any(keyword in error_msg.lower() for keyword in ["safety", "sensitive", "content policy", "nsfw"]):
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
            # ADIM 2: Video + Ses Birleştirme (Replicate)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # Voiceover ADIM 0'da üretildi. Burada sadece merge.
            if voiceover_succeeded and audio_url:
                try:
                    if progress_callback:
                        await progress_callback(
                            "step_3",
                            "🔀 Video ve dış ses birleştiriliyor (Replicate)..."
                        )
                    final_video_url = await self.replicate.async_merge_video_audio(
                        video_url=raw_video_url,
                        audio_url=audio_url,
                        replace_audio=False,  # Ambient sesler + Türkçe dış ses
                    )
                    log.info(f"Video+ses birleştirildi: {final_video_url[:60]}...")
                except Exception as merge_err:
                    log.error(
                        f"Merge hatası (graceful degradation): {merge_err}",
                        exc_info=True,
                    )
                    final_video_url = raw_video_url
                    voiceover_succeeded = False
                    result["voiceover_error"] = str(merge_err)[:300]
                    if progress_callback:
                        await progress_callback(
                            "merge_warning",
                            "⚠️ Ses birleştirme başarısız — video ambient seslerle teslim edilecek."
                        )
            else:
                if not voiceover_text:
                    log.warning("Dış ses metni boş — ses eklenmeden devam ediliyor")
                final_video_url = raw_video_url

            result["video_url"] = final_video_url
            result["status"] = "success"

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # ADIM 4: Notion güncelle — "Tamamlandı"
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            if notion_page_url:
                page_id = result.get("_notion_page_id") or self._extract_page_id(notion_page_url)
                if not page_id:
                    log.warning(
                        f"Notion page_id çıkarılamadı, 'Tamamlandı' güncellemesi atlandı: {notion_page_url}"
                    )
                else:
                    try:
                        # WHY: voiceover fail → "Tamamlandı (sessiz)" + error_message Notion'a yazılır
                        if voiceover_succeeded:
                            final_status = "Tamamlandı"
                            err_msg = ""
                        else:
                            final_status = "Tamamlandı (sessiz)"
                            err_msg = result.get("voiceover_error", "Dış ses üretimi/birleştirme başarısız")
                        await asyncio.to_thread(
                            self.notion.update_production_status,
                            page_id=page_id,
                            status=final_status,
                            video_url=final_video_url,
                            error_message=err_msg,
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
            
            # Hata sınıflandırması — kullanıcıya anlamlı mesaj
            user_facing_msg = error_msg
            if any(code in error_msg for code in ["512", "502", "503", "504", "500"]):
                user_facing_msg = (
                    "🔄 Video üretim servisi geçici olarak meşgul (upstream API hatası). "
                    "Otomatik yeniden deneme yapıldı ancak başarısız oldu. "
                    "Lütfen birkaç dakika sonra tekrar deneyin."
                )
                log.warning(f"Pipeline upstream API hatası (retry sonrası): {error_msg}")
            elif "timeout" in error_msg.lower() or "Polling timeout" in error_msg:
                user_facing_msg = (
                    "⏱️ Video üretimi zaman aşımına uğradı. "
                    "Sunucu yoğunluğu nedeniyle olabilir — lütfen tekrar deneyin."
                )
            elif "safety" in error_msg.lower() or "content policy" in error_msg.lower():
                user_facing_msg = (
                    "🛡️ İçerik güvenlik filtresi tetiklendi. "
                    "Farklı bir ürün/konsept ile tekrar deneyin."
                )
            
            result["error"] = error_msg
            log.error(f"Pipeline hatası: {error_msg}", exc_info=True)

            if notion_page_url:
                page_id = result.get("_notion_page_id") or self._extract_page_id(notion_page_url)
                if not page_id:
                    log.warning(
                        f"Notion page_id çıkarılamadı, 'Hata' güncellemesi atlandı: {notion_page_url}"
                    )
                else:
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
                await progress_callback("error", f"❌ {user_facing_msg[:200]}")

        return result

    # ── YARDIMCI ──

    @staticmethod
    def _extract_page_id(notion_url: str) -> str | None:
        """Notion page URL'inden page ID çıkar. WHY: 32-char olmazsa None — yanlış ID dönerek farklı page'i güncellemeyi önler."""
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
            return None
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

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🎬 MULTI-SCENE ÜRETİM (UGC Pipeline)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # UGC pipeline oturumundan (23 Nisan 2026) öğrenilen multi-scene akış.
    # 3 sahneyi paralel üretip lucataco/video-merge ile birleştirir.

    async def _produce_multi_scene(
        self,
        scenario: dict,
        reference_images: list,
        duration: int,
        aspect_ratio: str,
        progress_callback=None,
    ) -> str:
        """
        Multi-scene video üretim akışı.

        1. Her sahne için paralel Seedance 2.0 task'ı başlat
        2. Tüm sahneleri bekle (asyncio.gather)
        3. Replicate video-merge ile birleştir

        Args:
            scenario: UGC senaryo (scenes listesi içerir)
            reference_images: Ürün görselleri
            duration: Toplam video süresi
            aspect_ratio: Video formatı
            progress_callback: İlerleme callback'i

        Returns:
            str: Birleştirilmiş video URL'i
        """
        scenes = scenario.get("scenes", [])
        if not scenes:
            raise RuntimeError("Multi-scene senaryo 'scenes' listesi boş")

        scene_count = len(scenes)
        per_scene_duration = max(5, duration // scene_count)  # Minimum 5 saniye/sahne
        # WHY: gerçek üretilen toplam süre — cost calculation için scenario_engine ile aynı formül
        actual_total_duration = per_scene_duration * scene_count
        if actual_total_duration != duration:
            log.info(
                f"Multi-scene gerçek süre: {actual_total_duration}s "
                f"(senaryo {duration}s, {scene_count} × {per_scene_duration}s)"
            )

        if progress_callback:
            await progress_callback(
                "step_1",
                f"🎬 {scene_count} sahne paralel üretiliyor (Seedance 2.0)... "
                f"Bu 3-5 dakika sürebilir."
            )

        # No-dialogue güvenlik cümlesi
        no_dialogue = (
            "No character dialogue, no speaking, no lip movement. "
            "Enable ambient and environmental sounds, natural atmosphere."
        )

        # ── PARALEL SAHNE ÜRETİMİ ──
        async def _produce_single_scene(scene: dict, idx: int) -> str:
            """Tek sahneyi üretir ve video URL'ini döner.

            Reference image Seedance tarafından reddedilirse (örn. SVG/uzantısız OG image),
            otomatik olarak text-to-video moduna fallback yapar — sahne yine de üretilir.
            """
            prompt = scene.get("video_prompt", "")
            scene_name = scene.get("scene_name", f"Scene_{idx}")

            if "no dialogue" not in prompt.lower() and "no speaking" not in prompt.lower():
                prompt += f" {no_dialogue}"

            log.info(f"Sahne {idx+1}/{scene_count} başlatılıyor: {scene_name}")

            async def _run(use_refs: bool) -> dict:
                task = await asyncio.to_thread(
                    self.kie.create_video,
                    prompt=prompt,
                    duration=per_scene_duration,
                    aspect_ratio=aspect_ratio,
                    generate_audio=True,
                    reference_images=reference_images if (use_refs and reference_images) else None,
                )
                return await self.kie.async_poll_task(task)

            result = await _run(use_refs=True)

            # Reference image format hatası → text-to-video fallback
            if (
                result.get("status") != "success"
                and reference_images
                and "image format" in str(result.get("error", "")).lower()
            ):
                log.warning(
                    f"Sahne {idx+1}/{scene_count} ref_image reddedildi → text-to-video fallback: "
                    f"{result.get('error')}"
                )
                result = await _run(use_refs=False)

            if result["status"] != "success" or not result.get("urls"):
                error = result.get("error", "Bilinmeyen hata")
                raise RuntimeError(f"Sahne '{scene_name}' üretimi başarısız: {error}")

            url = result["urls"][0]
            log.info(f"Sahne {idx+1}/{scene_count} tamamlandı: {scene_name} → {url[:50]}...")
            return url

        # Paralel çalıştır — return_exceptions ile resource leak önle
        scene_tasks = [
            _produce_single_scene(scene, idx)
            for idx, scene in enumerate(scenes)
        ]
        results = await asyncio.gather(*scene_tasks, return_exceptions=True)

        # WHY: bir sahne fail etse bile diğerleri zaten üretildi — kullanılabilir olanı topla
        scene_video_urls: list[str] = []
        failed_count = 0
        for idx, res in enumerate(results):
            if isinstance(res, Exception):
                failed_count += 1
                log.error(f"Sahne {idx+1}/{scene_count} başarısız: {res}")
            elif isinstance(res, str) and res:
                scene_video_urls.append(res)

        if len(scene_video_urls) < 2:
            raise RuntimeError(
                f"{scene_count} sahneden {failed_count} başarısız oldu — "
                f"concat için yeterli sahne yok ({len(scene_video_urls)} başarılı)"
            )

        if failed_count > 0:
            log.warning(
                f"Multi-scene degraded mode: {len(scene_video_urls)}/{scene_count} sahne başarılı, "
                f"{failed_count} fail"
            )

        log.info(f"{len(scene_video_urls)} sahne hazır, concat başlıyor")

        # ── VIDEO CONCAT ──
        if progress_callback:
            await progress_callback(
                "step_1b",
                f"🔗 {scene_count} sahne birleştiriliyor..."
            )

        concat_url = await self.replicate.async_concat_videos(list(scene_video_urls))
        log.info(f"Multi-scene concat tamamlandı: {concat_url[:60]}...")

        return concat_url
