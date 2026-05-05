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
            # ADIM 0: VOICEOVER + KARAKTER GÖRSELİ — PARALEL
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # WHY: voiceover ses süresini, karakter görseli ise tüm sahnelerde
            # tutarlı karakteri sağlıyor. İkisi de senaryo çıktısına bağımlı,
            # birbirinden bağımsız → asyncio.gather ile paralel.
            voiceover_text = scenario.get("voiceover_text", "") or ""

            # ── NARRATIVE HOOK LOG (Dolunay görsün) ──
            _hook = (scenario.get("narrative_hook") or "").strip()
            if _hook:
                log.info(f"🧭 Narrative hook: {_hook}")
            else:
                log.warning("⚠️ Narrative hook eksik — voiceover/sahne paralelliği zayıf olabilir")

            # Voiceover kelime sayısı log (25 limit kontrolü — sadece konuşulan kelimeler)
            if voiceover_text:
                import re as _re_count
                # Audio tag'leri çıkar: [whispers], [pause], [delighted] vb.
                _spoken = _re_count.sub(r"\[[^\]]+\]", " ", voiceover_text)
                _word_count = len([w for w in _spoken.split() if w.strip()])
                _est_sec = _word_count / 2.5
                if _word_count > 25:
                    log.warning(
                        f"⚠️ Voiceover kelime sayısı limiti aştı: {_word_count} kelime "
                        f"(~{_est_sec:.1f}s) — LLM 25 kelime sınırına uymadı, kırpılacak"
                    )
                else:
                    log.info(
                        f"Voiceover kelime sayısı: {_word_count} kelime "
                        f"(~{_est_sec:.1f}s) — limit 25 ✅"
                    )

            # ── ZORLA KELİME KIRPMA (post-process) ──
            # WHY: LLM 25 kelime sınırına uymuyor → ses video'dan uzun çıkıyor.
            # Cümle bütünlüğünü koruyacak şekilde son cümleden başlayarak kırp.
            # Hedef: 25 kelime (~10s) → min 3 sahne (15s) videoya 5s tampon.
            if voiceover_text:
                from utils.text_normalizer import trim_voiceover_to_word_limit
                trimmed, orig_wc, final_wc, dropped = trim_voiceover_to_word_limit(
                    voiceover_text, max_words=25, min_words=18
                )
                if dropped > 0 or final_wc != orig_wc:
                    log.info(
                        f"Voiceover kırpıldı: {orig_wc} kelime → {final_wc} kelime "
                        f"({dropped} cümle atıldı)"
                    )
                    voiceover_text = trimmed
                    # Senaryoyu da güncelle ki audio_duration ölçümü doğru olsun
                    scenario["voiceover_text"] = trimmed

            # Türkçe sayı/yüzde/birim normalizasyonu — LLM "%10" yazsa bile düzelt
            if voiceover_text:
                from utils.text_normalizer import normalize_for_tts
                normalized = normalize_for_tts(voiceover_text)
                if normalized != voiceover_text:
                    log.info(
                        f"Voiceover normalize edildi: rakam/birim Türkçe yazıya çevrildi"
                    )
                    voiceover_text = normalized

            character_visual_prompt = (scenario.get("character_visual_prompt") or "").strip()
            character_visual_prompt_before = (scenario.get("character_visual_prompt_before") or "").strip()
            character_visual_prompt_after = (scenario.get("character_visual_prompt_after") or "").strip()
            narrative_pattern = (scenario.get("narrative_pattern") or "linear").strip().lower()
            character_gender = (scenario.get("character_gender") or "").strip()
            voice_name = (scenario.get("voice_name") or "Ahu").strip()
            # Ürün referans görseli — ilk geçerli ürün görselini kompozit için kullan
            product_image_for_composite = None
            if reference_images:
                product_image_for_composite = reference_images[0]

            async def _produce_voiceover():
                """Voiceover üret. Return: (audio_bytes, audio_url, audio_duration, success, err)."""
                if not voiceover_text:
                    return None, "", 0.0, True, ""
                try:
                    if progress_callback:
                        await progress_callback(
                            "step_voiceover",
                            "🎙️ Türkçe dış ses üretiliyor (ElevenLabs v3)..."
                        )
                    log.info(f"ElevenLabs TTS başlıyor: {len(voiceover_text)} karakter")
                    log.info(f"Voiceover voice: {voice_name} (LLM seçimi)")
                    ab = await asyncio.to_thread(
                        self.elevenlabs.generate_speech,
                        text=voiceover_text,
                        voice_name=voice_name,
                    )
                    from services.elevenlabs_service import ElevenLabsService
                    ad = ElevenLabsService.measure_audio_duration(ab)
                    log.info(f"Voiceover gerçek süresi: {ad:.2f}s")
                    au = await self.replicate.async_upload_audio(ab)
                    log.info(f"Dış ses Replicate storage'a yüklendi: {au[:80]}...")
                    return ab, au, ad, True, ""
                except Exception as vo_err:
                    log.error(
                        f"Dış ses üretim hatası (graceful degradation): {vo_err}",
                        exc_info=True,
                    )
                    if progress_callback:
                        await progress_callback(
                            "voiceover_warning",
                            "⚠️ Dış ses üretilemedi — video ambient seslerle teslim edilecek."
                        )
                    return None, "", 0.0, False, str(vo_err)[:300]

            async def _produce_character_image():
                """
                Karakter portresi(leri) üret. Pattern'e göre:
                - linear/reveal: tek karakter. Ürün ref'i varsa kompozit (karakter+ürün);
                  yoksa klasik text-to-image.
                - before_after/transformation: iki karakter (before + after). Before
                  text-to-image ile, after image-to-image ile before'dan üretilir
                  (aynı yüz korunsun). Ürün ref'i kompozite enjekte EDİLMEZ — burada
                  öncelik karakter cilt durumu tutarlılığı (Skincare).

                Dönüş: dict {
                    "main": <url|None>,
                    "before": <url|None>,
                    "after": <url|None>,
                }
                """
                out = {"main": None, "before": None, "after": None}
                if not (character_visual_prompt or character_visual_prompt_before):
                    log.info("character_visual_prompt boş — karakter üretimi atlanıyor (geriye dönük uyum)")
                    return out

                # ── DUAL KARAKTER (before/after) ──
                if narrative_pattern in {"before_after", "transformation"} and character_visual_prompt_before and character_visual_prompt_after:
                    try:
                        if progress_callback:
                            await progress_callback(
                                "step_character",
                                "👤 İki karakter varyantı üretiliyor (before + after)..."
                            )
                        log.info(
                            f"Dual karakter (pattern={narrative_pattern}, gender={character_gender or '?'}, "
                            f"voice={voice_name})"
                        )
                        log.info(f"  before prompt: {character_visual_prompt_before[:140]}...")
                        log.info(f"  after prompt:  {character_visual_prompt_after[:140]}...")

                        # 1) before portresi (text-to-image)
                        before_url = await self.kie.async_create_character_image(
                            prompt=character_visual_prompt_before,
                            aspect_ratio="9:16",
                            resolution="2K",
                        )
                        log.info(f"Karakter (before) üretildi: {before_url}")
                        out["before"] = before_url

                        # 2) after = before'dan i2i varyant (aynı yüz)
                        try:
                            after_url = await self.kie.async_create_character_variant_from_image(
                                base_image_url=before_url,
                                variant_prompt=character_visual_prompt_after,
                                aspect_ratio="9:16",
                            )
                            log.info(f"Karakter (after) üretildi (i2i variant): {after_url}")
                            out["after"] = after_url
                        except Exception as e2:
                            log.warning(
                                f"Karakter (after) i2i fail → text-to-image fallback: {e2}"
                            )
                            after_url = await self.kie.async_create_character_image(
                                prompt=character_visual_prompt_after,
                                aspect_ratio="9:16",
                                resolution="2K",
                            )
                            log.info(f"Karakter (after) üretildi (t2i fallback): {after_url}")
                            out["after"] = after_url

                        out["main"] = out["after"] or out["before"]
                        return out
                    except Exception as ce:
                        log.warning(
                            f"Dual karakter üretimi fail → linear fallback'a düşülüyor: {ce}",
                            exc_info=True,
                        )
                        # Linear flow'a düş

                # ── LINEAR / REVEAL (tek karakter) ──
                # Ürün ref'i varsa kompozit kullan; yoksa klasik
                base_prompt = character_visual_prompt or character_visual_prompt_before or character_visual_prompt_after
                if not base_prompt:
                    return out

                try:
                    if product_image_for_composite:
                        if progress_callback:
                            await progress_callback(
                                "step_character",
                                "👤 Karakter+ürün kompozit görsel üretiliyor (nano-banana-2 i2i)..."
                            )
                        log.info(
                            f"Karakter+ürün kompozit (gender={character_gender or '?'}, "
                            f"voice={voice_name}, product_ref={product_image_for_composite[:80]}...)"
                        )
                        cu = await self.kie.async_create_character_with_product(
                            character_prompt=base_prompt,
                            product_image_url=product_image_for_composite,
                            aspect_ratio="9:16",
                        )
                        log.info(f"Karakter+ürün kompozit görseli üretildi: {cu}")
                        out["main"] = cu
                        return out
                    else:
                        if progress_callback:
                            await progress_callback(
                                "step_character",
                                "👤 Karakter portresi üretiliyor (text-to-image)..."
                            )
                        log.info(
                            f"Karakter prompt (gender={character_gender or '?'}, voice={voice_name}, "
                            f"product_ref=YOK): {base_prompt[:140]}..."
                        )
                        cu = await self.kie.async_create_character_image(
                            prompt=base_prompt,
                            aspect_ratio="9:16",
                            resolution="2K",
                        )
                        log.info(f"Karakter görseli üretildi: {cu}")
                        out["main"] = cu
                        return out
                except Exception as ce:
                    log.warning(
                        f"Karakter görseli üretilemedi, ürün görselleriyle devam ediliyor: {ce}",
                        exc_info=True,
                    )
                    # Kompozit fail ise klasik text-to-image son şans
                    if product_image_for_composite:
                        try:
                            log.info("Kompozit fail → klasik text-to-image fallback")
                            cu = await self.kie.async_create_character_image(
                                prompt=base_prompt,
                                aspect_ratio="9:16",
                                resolution="2K",
                            )
                            out["main"] = cu
                            log.info(f"Karakter (fallback) üretildi: {cu}")
                        except Exception as ce2:
                            log.warning(f"Karakter fallback de fail: {ce2}")
                    return out

            (vo_bytes, audio_url, audio_duration, voiceover_succeeded, vo_err_msg), character_images = (
                await asyncio.gather(_produce_voiceover(), _produce_character_image())
            )
            character_image_url = character_images.get("main")
            character_before_url = character_images.get("before")
            character_after_url = character_images.get("after")

            if audio_url:
                result["audio_url"] = audio_url
            if vo_err_msg:
                result["voiceover_error"] = vo_err_msg

            # WHY: Seedance reference'ı tek bir KARAKTER+ÜRÜN kompozit görseliyle
            # besliyoruz. Bu kompozit hem karakter tutarlılığını hem ürün doğruluğunu
            # garanti ediyor (Air Force 1 yerine yanlış model çıkması probleminin çözümü).
            # before_after pattern'da her sahnenin character_state'ine göre doğru
            # portreyi (before veya after) referans olarak vereceğiz.
            product_image_urls = list(reference_images or [])
            state_to_ref: dict[str, str] = {}
            if character_before_url:
                state_to_ref["before"] = character_before_url
            if character_after_url:
                state_to_ref["after"] = character_after_url
            # transitional → after varyantı (yoksa before)
            if character_after_url:
                state_to_ref["transitional"] = character_after_url
            elif character_before_url:
                state_to_ref["transitional"] = character_before_url
            # Tek karakter modunda main URL fallback olarak tüm state'leri karşılar
            if character_image_url and not state_to_ref:
                state_to_ref = {
                    "before": character_image_url,
                    "after": character_image_url,
                    "transitional": character_image_url,
                }

            if character_image_url:
                reference_images = [character_image_url]
                if state_to_ref and (character_before_url or character_after_url):
                    log.info(
                        f"Referans görseller hazır: dual karakter (pattern={narrative_pattern}) — "
                        f"before={'✓' if character_before_url else '✗'}, "
                        f"after={'✓' if character_after_url else '✗'} | "
                        f"{len(product_image_urls)} ürün görseli prompt'a bırakıldı"
                    )
                else:
                    log.info(
                        f"Referans görseller hazır: 1/1 (karakter+ürün kompozit) — "
                        f"{len(product_image_urls)} ürün görseli prompt'a bırakıldı, "
                        f"Seedance'a referans olarak gönderilmiyor (kompozit görselde zaten var)"
                    )
            else:
                reference_images = product_image_urls[:9]
                log.warning(
                    f"Karakter görseli üretilemedi → fallback: {len(reference_images)} "
                    f"ürün görseli referans olarak kullanılacak"
                )

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # SES-VIDEO SYNC: Akıllı 3-Katman
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # KÖKLÜ ÇÖZÜM:
            # Katman A: Senaryo aşamasında validation — LLM ≥4 sahne yazmaya zorlandı
            #           (scenario_engine quality validation), 5 sahne planlıyor (system prompt).
            # Katman B: Ses ölçüldükten sonra ratio (audio/llm_target) kontrolü:
            #   B1) ratio ≤ 1.05+tolerans: müdahale yok, mevcut akış
            #   B2) 1.05 < ratio ≤ 1.25: KOMPRES dene (kabul edilebilir konuşma yoğunluğu)
            #   B3) ratio > 1.25: KOMPRES YAPMA (TTS çıktısı çok yoğun/hızlı algılanır),
            #                     direkt video uzatmaya geç
            # Katman C: Video uzatma (ses uzun + LLM scenes yetersiz):
            #   - LLM'den GERÇEK ek payoff sahne(leri) iste (URL duplicate YOK)
            #   - Seedance'a yeni render → görsel çeşitlilik korunur
            import math
            scenes_list_raw = scenario.get("scenes") or []
            llm_scene_count = len(scenes_list_raw)

            llm_target_duration = max(1, llm_scene_count) * 5
            SYNC_TOLERANCE = 1.5      # ses video+1.5s'i aşarsa müdahale
            COMPRESS_MAX_RATIO = 1.25  # bu oranın üstünde kompres devre dışı

            ratio = (audio_duration / llm_target_duration) if (audio_duration > 0 and llm_target_duration > 0) else 0
            needs_intervention = (
                voiceover_succeeded
                and audio_duration > 0
                and audio_duration > llm_target_duration + SYNC_TOLERANCE
            )

            # ── KATMAN B2: KOMPRES (ratio ≤ 1.25) ──
            if needs_intervention and ratio <= COMPRESS_MAX_RATIO and voiceover_text:
                target_words = max(8, int(llm_target_duration * 2.5) - 2)
                log.warning(
                    f"⚠️ Ses {audio_duration:.1f}s > video {llm_target_duration}s "
                    f"(ratio {ratio:.2f}x ≤ {COMPRESS_MAX_RATIO} sınırı) → "
                    f"metin {target_words} kelimeye sıkıştırılıyor"
                )
                if progress_callback:
                    await progress_callback(
                        "voiceover_resync",
                        f"🎚️ Ses biraz uzun ({audio_duration:.0f}s) — metni "
                        f"sıkıştırıp tekrar sentezliyorum..."
                    )
                try:
                    compressed_text = await self._compress_voiceover(
                        voiceover_text, target_words=target_words
                    )
                    if compressed_text and compressed_text.strip() != voiceover_text.strip():
                        new_bytes = await asyncio.to_thread(
                            self.elevenlabs.generate_speech,
                            text=compressed_text,
                            voice_name=voice_name,
                        )
                        from services.elevenlabs_service import ElevenLabsService as _EL
                        new_duration = _EL.measure_audio_duration(new_bytes)
                        log.info(f"Sıkıştırılmış ses: {new_duration:.2f}s (önceki {audio_duration:.2f}s)")
                        if new_duration > 0 and new_duration < audio_duration:
                            new_url = await self.replicate.async_upload_audio(new_bytes)
                            voiceover_text = compressed_text
                            audio_duration = new_duration
                            audio_url = new_url
                            scenario["voiceover_text"] = compressed_text
                            result["audio_url"] = audio_url
                            log.info(f"✅ Ses sıkıştırıldı: {audio_duration:.1f}s")
                    else:
                        log.warning("Kompres başarısız (LLM aynı/boş döndü)")
                except Exception:
                    log.warning("Kompres katmanı başarısız", exc_info=True)
            elif needs_intervention and ratio > COMPRESS_MAX_RATIO:
                log.warning(
                    f"⚠️ Ses {audio_duration:.1f}s, ratio {ratio:.2f}x > {COMPRESS_MAX_RATIO} → "
                    f"kompres yerine video uzatma katmanına geçiliyor (konuşma yoğunluğu sınırı)"
                )

            # ── KATMAN C: SAHNE SAYISI (gerekirse LLM'den ek sahne) ──
            # WHY: Kompres sonrası (veya kompres yapılmadıysa) ses süresine göre sahne
            # sayısını belirle. Eğer LLM'in planladığı sahneler yetmiyorsa GERÇEK yeni
            # sahne(ler) üret — URL duplicate kullanma.
            if audio_duration > 0:
                ideal_scene_count = max(3, math.ceil(audio_duration / 5))
                final_scene_count = max(1, ideal_scene_count)
                duration = final_scene_count * 5
            else:
                final_scene_count = max(1, min(llm_scene_count, 5)) if llm_scene_count else 3
                duration = final_scene_count * 5
                log.info(
                    f"Voiceover ölçülemedi, varsayılan sahne sayısı: {final_scene_count} "
                    f"(LLM planı {llm_scene_count})"
                )

            # Sahne listesini final_scene_count'a uydur
            if scenes_list_raw:
                if final_scene_count <= llm_scene_count:
                    # LLM yeterli — ilk N sahneyi al
                    scenario["scenes"] = scenes_list_raw[:final_scene_count]
                    log.info(
                        f"Sahne planı: {final_scene_count}/{llm_scene_count} sahne kullanılacak "
                        f"(ses {audio_duration:.1f}s, video {duration}s)"
                    )
                else:
                    # LLM yetmiyor — GERÇEK ek sahne(ler) üret
                    extra_needed = final_scene_count - llm_scene_count
                    log.warning(
                        f"📐 Video uzatma: LLM {llm_scene_count} sahne planladı, "
                        f"{final_scene_count} lazım → {extra_needed} ek sahne LLM'den isteniyor"
                    )
                    if progress_callback:
                        await progress_callback(
                            "scene_extend",
                            f"📐 Ses uzun çıktı — {extra_needed} ek payoff sahnesi üretiyorum..."
                        )
                    try:
                        extra_scenes = await self._generate_extra_scenes(
                            scenario=scenario,
                            count_needed=extra_needed,
                            collected_data=collected_data,
                        )
                        if extra_scenes and len(extra_scenes) >= 1:
                            scenes_list_raw = list(scenes_list_raw) + list(extra_scenes)
                            scenario["scenes"] = scenes_list_raw
                            # Yeniden hesapla (LLM eksik sahne döndüyse)
                            final_scene_count = len(scenes_list_raw)
                            duration = final_scene_count * 5
                            log.info(
                                f"✅ {len(extra_scenes)} ek sahne üretildi → toplam {final_scene_count} sahne"
                            )
                        else:
                            log.warning(
                                "Ek sahne üretilemedi → LLM'in mevcut sahneleriyle yetinilecek "
                                "(ses video'yu az aşabilir)"
                            )
                            scenario["scenes"] = scenes_list_raw
                            final_scene_count = llm_scene_count
                            duration = final_scene_count * 5
                    except Exception:
                        log.warning(
                            "Ek sahne üretimi exception → mevcut sahnelerle devam",
                            exc_info=True,
                        )
                        scenario["scenes"] = scenes_list_raw
                        final_scene_count = llm_scene_count
                        duration = final_scene_count * 5

            scenario["scene_count"] = final_scene_count
            scenario["is_multi_scene"] = final_scene_count > 1

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # ADIM 1: VIDEO ÜRETİMİ
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            multi_succeeded_count = 0
            multi_per_scene_duration = 0
            if scenario.get("is_multi_scene"):
                raw_video_url, multi_succeeded_count, multi_per_scene_duration = await self._produce_multi_scene(
                    scenario=scenario,
                    reference_images=reference_images,
                    duration=duration,
                    aspect_ratio=aspect_ratio,
                    progress_callback=progress_callback,
                    state_to_ref=state_to_ref,
                )
                result["raw_video_url"] = raw_video_url
                log.info(
                    f"Multi-scene video üretildi: {raw_video_url[:60]}... "
                    f"({multi_succeeded_count} sahne × {multi_per_scene_duration}s)"
                )
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
            #
            # SYNC KORUYUCU: Multi-scene degraded mode'da (örn. 1 sahne copyright fail)
            # gerçek video süresi planlananın altına düşer. duration_mode="audio" olursa
            # video kalan ses süresince freeze eder. Bu durumda duration_mode="video"
            # kullanıp sesi video boyuna kırpıyoruz (mesajın sonu kesilebilir ama sync OK).
            duration_mode = "audio"
            if scenario.get("is_multi_scene") and multi_succeeded_count and multi_per_scene_duration:
                actual_video_duration = multi_succeeded_count * multi_per_scene_duration
                if voiceover_succeeded and audio_duration > actual_video_duration + 0.5:
                    duration_mode = "video"
                    log.warning(
                        f"Degraded multi-scene sync koruyucu: ses {audio_duration:.1f}s, "
                        f"video {actual_video_duration}s → duration_mode=video (ses video boyuna kırpılacak)"
                    )

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
                        duration_mode=duration_mode,
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
    async def _generate_extra_scenes(
        scenario: dict,
        count_needed: int,
        collected_data: dict,
    ) -> list[dict]:
        """LLM'den N adet GERÇEK ek payoff sahnesi üret.

        WHY: Ses LLM'in planladığı süreden çok uzun çıktığında (kompres yapamadığımız
        veya yetmediği durumlarda), aynı sahneyi URL duplicate ile tekrarlamak yerine
        LLM'den GERÇEK yeni payoff sahneleri üretiyoruz. Görsel çeşitlilik korunur,
        karakter ve marka tutarlılığı garanti edilir.

        Args:
            scenario: Mevcut senaryo (zaten üretilmiş sahneler dahil)
            count_needed: Kaç yeni sahne lazım (1-3 arası tipik)
            collected_data: Marka/ürün bilgisi (URLDataExtractor çıktısı)

        Returns:
            list[dict]: Ek sahnelerin listesi. Her sahne: scene_name, video_prompt,
                        voiceover_segment, character_state alanlarıyla.
                        Hata durumunda boş liste.
        """
        if count_needed <= 0:
            return []

        import openai
        import os
        import json as _json

        existing_scenes = scenario.get("scenes") or []
        char_prompt = (scenario.get("character_visual_prompt") or "").strip()
        char_after = (scenario.get("character_visual_prompt_after") or "").strip()
        char_visual_for_context = char_prompt or char_after or "(karakter prompt yok)"

        narrative_pattern = scenario.get("narrative_pattern") or "linear"
        brand = collected_data.get("brand_name", "")
        product = collected_data.get("product_name", "")

        existing_summary_lines = []
        for idx, sc in enumerate(existing_scenes, 1):
            name = sc.get("scene_name", f"Scene_{idx}")
            seg = sc.get("voiceover_segment", "")
            existing_summary_lines.append(f"  {idx}. {name} — segment: \"{seg[:80]}\"")
        existing_summary = "\n".join(existing_summary_lines) if existing_summary_lines else "(yok)"

        system_msg = (
            "Sen TikTok/Reels native ad strategist'sin. Verilen senaryonun mevcut "
            "sahnelerinin DEVAMINA, AYNI karakter ve AYNI ürünle, payoff (final) odaklı "
            f"{count_needed} yeni sahne üreteceksin.\n\n"
            "KURALLAR:\n"
            "1. Her sahne 5 saniyelik bağımsız bir Seedance shot olarak çekilebilmeli.\n"
            "2. AYNI karakter — yaş/cinsiyet/saç/kıyafet hepsi aynı (referans aşağıda).\n"
            "3. Mevcut sahnelerden FARKLI mekan VEYA farklı kamera açısı (tekrar yok).\n"
            "4. Ürünün kendisi her sahnede net görünmeli — alakasız nesneye sapma.\n"
            "5. character_state DAİMA \"after\" (payoff sahneleri).\n"
            "6. video_prompt İNGİLİZCE, şu cümleyle başlamalı: "
            "\"The EXACT same person from the reference image (do not generate a different "
            "person — same face, hair, outfit, build):\"\n"
            "7. UGC creator footage tonu — handheld iPhone, real skin texture, phone sensor grain. "
            "STÜDYO/CINEMATIC YASAK.\n"
            "8. voiceover_segment ARTIK SES METNİNDEN GELMEYECEK — bu sahneler ses bittikten "
            "sonra ekrana ürünün kalmasını sağlamak için. voiceover_segment ALANINI BOŞ STRİNG (\"\") "
            "olarak döndür — bu sahneler sessiz ürün anları.\n"
            "9. JSON formatı: {\"scenes\": [{\"scene_name\": \"...\", \"video_prompt\": \"...\", "
            "\"voiceover_segment\": \"\", \"character_state\": \"after\"}, ...]}"
        )

        user_msg = (
            f"## Mevcut Senaryo:\n"
            f"- Marka: {brand}\n"
            f"- Ürün: {product}\n"
            f"- Narrative pattern: {narrative_pattern}\n"
            f"- Karakter (ANY referans): {char_visual_for_context[:300]}...\n\n"
            f"## Mevcut sahneler:\n{existing_summary}\n\n"
            f"## Görev:\n"
            f"Yukarıdaki sahnelerin DEVAMINA gelecek {count_needed} ek payoff sahnesi üret. "
            f"Her biri ürünü farklı bir açıdan/mekanda gösteren, sessiz, son izlenim odaklı sahne olsun. "
            f"voiceover_segment alanlarını BOŞ STRİNG bırak (sessiz ürün shotları)."
        )

        try:
            client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg},
                ],
                max_completion_tokens=1500,
                response_format={"type": "json_object"},
            )
            content = (response.choices[0].message.content or "").strip()
            data = _json.loads(content) if content else {}
            extra = data.get("scenes") or []
            if not isinstance(extra, list):
                return []

            valid_scenes = []
            for sc in extra[:count_needed]:
                if not isinstance(sc, dict):
                    continue
                vp = (sc.get("video_prompt") or "").strip()
                if not vp:
                    continue
                valid_scenes.append({
                    "scene_name": (sc.get("scene_name") or "Extra Payoff").strip()[:60],
                    "video_prompt": vp,
                    "voiceover_segment": (sc.get("voiceover_segment") or "").strip(),
                    "character_state": "after",
                })
            return valid_scenes
        except Exception as e:
            from logger import get_logger
            get_logger("production_pipeline").error(
                f"Ek sahne üretim hatası: {e}", exc_info=True
            )
            return []

    @staticmethod
    async def _compress_voiceover(original_text: str, target_words: int) -> str:
        """Voiceover metnini hedef kelime sayısına sıkıştır.

        WHY: Ses video'dan uzun çıktığında, dumb-trim son cümleyi (PAYOFF) keser.
        Burada LLM'e "anlamı koru, son cümleyi koru, audio tag'ler hariç X kelime"
        diyerek akıllı sıkıştırma yaptırıyoruz.

        Args:
            original_text: Orijinal voiceover (audio tag'ler dahil)
            target_words: Hedef kelime sayısı (audio tag'ler hariç)

        Returns:
            str: Sıkıştırılmış metin, ya da boş string (başarısızsa)
        """
        import openai
        import os
        try:
            client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model="gpt-4.1-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Sen bir Türkçe reklam metni editörüsün. Verilen voiceover "
                            "metnini hedef kelime sayısına SIKIŞTIRACAKSIN. KURALLAR:\n"
                            "1. SON CÜMLE (PAYOFF) MUTLAKA KORUNUR — kısaltabilirsin ama atlama.\n"
                            "2. Hedef kelime sayısı: audio tag'ler ([whispers], [pause], "
                            "[delighted] vb.) HARİÇ konuşulan Türkçe kelimeler.\n"
                            "3. 1. tekil şahıs ton korunur (ben/benim/-yorum).\n"
                            "4. Audio tag'ler korunur ama gerekiyorsa azaltılabilir.\n"
                            "5. Anlam ve hikaye akışı bozulmaz.\n"
                            "6. SADECE sıkıştırılmış metni döndür, açıklama yazma."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Hedef kelime sayısı (audio tag'ler hariç): {target_words}\n\n"
                            f"Orijinal metin:\n{original_text}\n\n"
                            f"Sıkıştırılmış metin:"
                        ),
                    },
                ],
                max_completion_tokens=400,
            )
            compressed = (response.choices[0].message.content or "").strip()
            if compressed.startswith("```"):
                lines = [ln for ln in compressed.split("\n") if not ln.startswith("```")]
                compressed = "\n".join(lines).strip()
            return compressed
        except Exception as e:
            from logger import get_logger
            get_logger("production_pipeline").error(
                f"Voiceover sıkıştırma hatası: {e}", exc_info=True
            )
            return ""

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
        state_to_ref: dict | None = None,
    ) -> tuple[str, int, int]:
        """
        Multi-scene video üretim akışı.

        1. Her sahne için paralel Seedance 2.0 task'ı başlat
        2. Fail eden sahneleri safety rewrite + image-format fallback ile kurtar
        3. Tüm sahneleri bekle (asyncio.gather)
        4. Replicate video-merge ile birleştir

        Returns:
            (concat_url, succeeded_scene_count, per_scene_duration)
            — caller degraded mode tespit edip ses senkronu için kullanır.
        """
        scenes = scenario.get("scenes", [])
        if not scenes:
            raise RuntimeError("Multi-scene senaryo 'scenes' listesi boş")

        # Seedance design: her sahne 5s sabit. Tüm sahneler GERÇEK render edilir
        # (URL duplicate yok — ses uzunsa scenes listesi LLM'den ek sahne ile uzatılmış).
        per_scene_duration = 5
        scene_count = len(scenes)
        log.info(f"Multi-scene plan: {scene_count} sahne × {per_scene_duration}s = {scene_count * per_scene_duration}s video")

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

            character_state varsa state_to_ref'ten doğru karakter portresini ref olarak verir
            (before_after pattern desteği).
            """
            prompt = scene.get("video_prompt", "")
            scene_name = scene.get("scene_name", f"Scene_{idx}")
            scene_state = (scene.get("character_state") or "").strip().lower()

            # State'e göre doğru ref'i seç; yoksa default reference_images
            scene_refs = list(reference_images) if reference_images else []
            if state_to_ref and scene_state and scene_state in state_to_ref:
                state_ref_url = state_to_ref[scene_state]
                if state_ref_url:
                    scene_refs = [state_ref_url]
                    log.info(
                        f"Sahne {idx+1}/{scene_count} character_state='{scene_state}' → "
                        f"ref={state_ref_url[:80]}..."
                    )

            if "no dialogue" not in prompt.lower() and "no speaking" not in prompt.lower():
                prompt += f" {no_dialogue}"

            log.info(f"Sahne {idx+1}/{scene_count} başlatılıyor: {scene_name} (state={scene_state or '?'})")

            async def _run(use_refs: bool) -> dict:
                task = await asyncio.to_thread(
                    self.kie.create_video,
                    prompt=prompt,
                    duration=per_scene_duration,
                    aspect_ratio=aspect_ratio,
                    generate_audio=True,
                    reference_images=scene_refs if (use_refs and scene_refs) else None,
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

            # Safety/copyright/sensitive content → prompt rewrite + retry
            # WHY: Tek başarısız sahne tüm video'nun ses senkronunu bozabiliyor.
            err_str = str(result.get("error", "")).lower()
            if (
                result.get("status") != "success"
                and any(kw in err_str for kw in ["safety", "copyright", "sensitive", "content policy", "nsfw"])
            ):
                log.warning(
                    f"Sahne {idx+1}/{scene_count} safety/copyright filtreye takıldı, prompt rewrite deneniyor: "
                    f"{result.get('error')}"
                )
                try:
                    rewritten = await self._rewrite_prompt_for_safety(prompt)
                    if rewritten and rewritten != prompt:
                        original_prompt = prompt
                        prompt = rewritten + " " + no_dialogue
                        result = await _run(use_refs=True)
                        # Rewrite + ref image hâlâ fail ediyorsa, ref'siz dene
                        if (
                            result.get("status") != "success"
                            and reference_images
                            and "image format" in str(result.get("error", "")).lower()
                        ):
                            result = await _run(use_refs=False)
                        prompt = original_prompt  # diagnostic için
                except Exception as rewrite_err:
                    log.warning(f"Sahne {idx+1} safety rewrite başarısız: {rewrite_err}")

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

        if len(scene_video_urls) < 1:
            raise RuntimeError(
                f"{scene_count} sahneden TÜM SAHNELER başarısız oldu — "
                f"concat için en az 1 başarılı sahne gerek"
            )

        # SAHNE FAIL FILLER — akıllı tekrar (ses-video sync için)
        # WHY: scene_count'u koruruz çünkü voiceover scene_count*per_scene_duration'a göre
        # planlandı. Sahne kısalırsa ses video'dan uzun kalır → kesilir.
        # Strateji: failed sahnelerin SAYISI kadar, başarılı sahnelerden TÜR'üne göre
        # tekrar ekle (orta sahne öncelikli — HOOK'u tekrarlamak izleyici dikkati için kötü).
        # Maksimum 1 tekrar (2+ fail durumunda yine düşürülür).
        if failed_count > 0:
            actual_count = len(scene_video_urls)
            if actual_count < 2:
                raise RuntimeError(
                    f"{scene_count} sahneden sadece {actual_count} başarılı — "
                    f"minimum 2 sahne gerek (tekrar dene)"
                )
            # 1 sahne eksikse: ortadaki başarılı sahneyi 1 kez listenin sonuna ekle
            # (HOOK'u tekrar etmek yerine — ortadaki sahne PAYOFF olur)
            missing = scene_count - actual_count
            if missing == 1 and actual_count >= 2:
                filler_idx = len(scene_video_urls) // 2  # orta sahne
                scene_video_urls.append(scene_video_urls[filler_idx])
                log.warning(
                    f"Multi-scene filler: {actual_count}/{scene_count} sahne başarılı, "
                    f"1 fail → orta sahne (idx={filler_idx}) tekrar eklendi → "
                    f"video {scene_count} sahnede ({scene_count * per_scene_duration}s) kalır"
                )
            else:
                log.warning(
                    f"Multi-scene degraded mode: {actual_count}/{scene_count} sahne başarılı, "
                    f"{failed_count} fail (filler max 1) → video "
                    f"{actual_count} sahneye düştü ({actual_count * per_scene_duration}s)"
                )

        log.info(f"{len(scene_video_urls)} sahne hazır, concat başlıyor")

        # ── VIDEO CONCAT ──
        if progress_callback:
            await progress_callback(
                "step_1b",
                f"🔗 {len(scene_video_urls)} sahne birleştiriliyor..."
            )

        concat_url = await self.replicate.async_concat_videos(list(scene_video_urls))
        log.info(f"Multi-scene concat tamamlandı: {concat_url[:60]}...")

        # WHY: scene_video_urls tekrarlarla scene_count'a tamamlandı → toplam süre tam.
        return concat_url, len(scene_video_urls), per_scene_duration
