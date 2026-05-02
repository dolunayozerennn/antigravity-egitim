---
description: Bu oturumda Gemini ile yapılan planlamayı/araştırmayı, terminaldeki Claude Code'a yapıştırılmaya hazır tek bir prompt halinde paketle. Kullanıcı planlamayı Antigravity'de yaptıktan sonra implementation/deploy işini Claude Code CLI'a devretmek istediğinde tetiklenir.
---

# 🤝 Claude Code Handover

> **Amaç:** Bu konuşmadaki planı, kararları ve bağlamı Claude Code'a (terminal) **kopyala-yapıştır promptu** olarak ver. Kullanıcının elinden minimum iş geçsin.

---

## Adım 1 — Bağlamı Topla

Şu kaynakları sessizce gözden geçir (kullanıcıya tek tek raporlama):

1. **Bu konuşma** — son ~20 mesaj içinde neyi konuştuk, hangi karara vardık, hangi planı çıkardık?
2. **Aktif proje patiği** — kullanıcı bir proje üzerinde mi çalışıyor? Hangisi? `Projeler/<x>/` veya başka bir konum?
3. **Git durumu** — değişmiş ama commit edilmemiş dosyalar var mı? Hangi branch'tayız? (`git status`, `git log -3 --oneline`)
4. **Açık plan dosyaları** — `Projeler/<x>/PLAN.md`, `DEPLOY_PLAN.md` veya benzeri var mı? İçinde işlenecek madde var mı?
5. **İlgili skill/workflow** — yapılacak iş hangi skill'e tetikleniyor? (deploy → `canli-yayina-al`, mail → `eposta-gonderim`, fatura → `fatura-olusturucu` vb.)
6. **İlgili knowledge** — `_knowledge/` altında bu işle ilgili okunması gereken dosya var mı? (deploy ise `deploy-registry.md`, hata ise `hatalar-ve-cozumler.md` vb.)
7. **Açık sorular** — konuşmada cevaplanmamış, Claude Code'un kullanıcıya sorması gereken karar var mı?

---

## Adım 2 — Promptu Üret

Aşağıdaki **tek bir markdown code block** olarak çıktı ver. Block dışına hiçbir şey yazma — kullanıcı triple-backtick içeriğini olduğu gibi yapıştıracak. Block başına ve sonuna açıklama, "buyrun", "umarım faydalı olur" gibi şeyler **yazma**.

Format:

````markdown
# Görev: <bir cümlelik özet>

## Bağlam
<3-5 satır: ne yaptık, neyi planladık, şu anda ne durumdayız>

## Çalışılan Yer
- **Proje:** `Projeler/<x>/` (yoksa: workspace root)
- **Branch:** `<branch-adı>` (uncommitted: var/yok)
- **Plan dosyası (varsa):** `Projeler/<x>/PLAN.md`

## Yapılması İstenen
<sıralı maddeler — her madde somut, ölçülebilir bir adım. "Şunu güzelleştir" gibi muğlak değil, "X dosyasında Y fonksiyonunu Z şekilde değiştir" gibi net.>

1. ...
2. ...
3. ...

## Tetiklenmesi Beklenen Skill / Workflow
- `<skill-adı>` — neden
- (varsa) `/<workflow>` — neden

## Okunması Gereken Bağlam
- `_knowledge/<dosya>.md` — neden
- `_skills/<x>/SKILL.md` — neden
- (varsa) `Projeler/<x>/<dosya>` — neden

## Açık Sorular (uygulamaya başlamadan kullanıcıya sor)
<varsa madde madde; yoksa "Yok, doğrudan başla" yaz>

## Bitişte Beklenen Çıktı
<deploy ise: "_knowledge/deploy-registry.md güncellensin, commit atılsın", kod ise: "test geçsin, commit atılsın", vb.>

## Notlar
- Bu görev Antigravity-Gemini oturumunda planlandı, uygulama Claude Code'a devredildi.
- Kullanıcı otonom çalışma istiyor — terminal komutlarını sen çalıştır, "şunu yapıştır" deme.
- Çalışma dili Türkçe.
````

---

## Adım 3 — Teslim Et

Promptu yazdıktan sonra kullanıcıya tek satır söyle:

> *"Hazır. Yukarıdaki bloğu kopyala, yeni bir terminalde `claude` aç ve yapıştır."*

**Daha fazla açıklama yapma**, "şu da olabilir" gibi alternatifler ekleme. Kullanıcı zaten oturuma minimum iş yapmak için geldi.

---

## Önemli Kurallar

- **Master.env içeriğini, API anahtarını, token'ı promptun içine yazma** — Claude Code zaten `_knowledge/credentials/master.env`'e doğrudan erişebiliyor.
- **Kod parçası kopyalama** — promptun içinde uzun kod block'ları olmasın; bunun yerine "şu dosyayı oku" referansı yeterli.
- **Bağlam yetersizse** prompt üretmeden önce kullanıcıya bir-iki kısa soru sor (örn. "Hangi projede çalışıyoruz?", "PLAN.md var mı?"). Tahmin yürütme.
- **"Promptu doğru üretip üretmediğini" sorma** — direkt üret. Kullanıcı yanlışsa kendi düzeltir.
