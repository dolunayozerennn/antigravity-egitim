---
name: proje-gorsellestirici
description: Tamamlanmış bir projeyi veya otomasyon sürecini teknik olmayan, ManyChat tarzında şık, yatay (soldan sağa akan) ve az metinli bir HTML arayüzüne dönüştürür.
---

# Proje Görselleştirici (Project Visualizer)

**Amaç:** Kullanıcının geliştirdiği kod veya otomasyon tabanlı projeleri, sosyal medyada gösterilebilecek ve müşterilere (işletme sahiplerine) teslim edilebilecek **görsel, teknik olmayan, premium bir akış şemasına** dönüştürmek. ManyChat platformundaki gibi **soldan sağa doğru akan, az metinli ve net düğümler (nodes)** üzerinden görselleştirme sağlanır. Uzay (Space) tuşuna veya sağ yön tuşuna basıldıkça sıra sıra yanan şık adımlar gösterilir.

## Yönergeler

Kullanıcı senden bir projenin görselleştirilmesini istediğinde şu adımları uygula:

1. **Projeyi Analiz Et:**
   - Hedef projenin çalışma prensibini anla.
   - Tamamen **günlük, ticari ve teknik olmayan** bir dil kullan. *Asla kodlama terimleri, API, Server vb. kelimeler kullanma.*
   - Metinleri **olabildiğince kısa ve öz (ManyChat netliğinde)** tut. Uzun açıklamalar yerine, ne yapıldığını anında kavratacak 2-3 kelimelik özetler seç.

2. **Şablon Değişkenlerini Hazırla:**
   - **`{{PROJECT_NAME}}`**: Etkileyici ve kısa bir başlık (Örn: "Otonom E-Posta Asistanı").
   - **`{{PROJECT_DESCRIPTION}}`**: Projenin sonucunu / faydasını özetleyen tek cümlelik bir alt başlık.
   - **Adımlar (Nodes):** Projeyi 3 ila 6 temel adıma böl. Her adım için:
     - `title`: Adımın kısa başlığı (örn: "Gelen Kutusu", "Karar Mekanizması")
     - `desc`: Çok kısa, 1-2 cümlelik basit bir açıklama.
     - `icon`: Uygun bir emoji (Örn: ⚡, ✉️, 🤖, 🧠, 🚀, ⚙️)
     - `subSteps`: İşlem yapıldığını gösteren animasyonlu alt başlıklar. Array halinde sırala. Sadece 1-3 kelimelik ("Mailler okundu", "Müşteri analiz edildi" gibi) net ifadeler kullan. Uzun uzun yazma.

3. **Şablonu Oku ve Birleştir:**
   - `_skills/proje-gorsellestirici/resources/template.html` şablonunu oku. (Bu şablon halihazırda soldan sağa doğru akan, ManyChat tarzı karanlık temalı yatay akış mantığıyla kodlanmıştır.)
   - `{{PROJECT_NAME}}` ve `{{PROJECT_DESCRIPTION}}` placeholder'larını değiştir.
   - Dosya içindeki script etiketinin altında bulunan `/*__NODES_DATA__*/` ile `/*__NODES_DATA_END__*/` aralığını bularak, aradaki array yapısını tamamen silip, kendi hazırladığın adımları Javascript array formatında yaz:
   ```javascript
   [
       { 
           title: '...', 
           desc: '...', 
           icon: '...',
           subSteps: ['...', '...', '...']
       },
       // diğer adımlar...
   ]
   ```

4. **Dosyayı Proje Klasörüne Kaydet:**
   - Sonuçta ortaya çıkan HTML dosyasını, hedef proje klasörüne `Proje_Akisi.html` veya `Sistem_Nasil_Calisir.html` ismiyle kaydet.

5. **Kullanıcı Bilgilendirmesi:**
   - Kullanıcıya işlemin tamamlandığını, HTML dosyasının yolunu vererek tıklayıp tarayıcıda açabileceğini bildir.
   - Videoda anlatım yaparken "Space" (boşluk) veya "Sağ Ok" tuşu ile adımları sırayla (ManyChat tarzında) ilerleterek gösterebileceğini hatırlat.
