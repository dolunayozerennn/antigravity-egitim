import sys
from ops_logger import get_ops_logger
from core.post_writer import PostWriter
from core.image_generator import ImageGenerator
from core.linkedin_publisher import LinkedInPublisher

ops = get_ops_logger("LinkedIn_Text_Paylasim", "LIVE_TEST")

def test_pipeline():
    ops.info("LIVE TEST", "LinkedIn Uçtan Uca Paylaşım Testi Başlıyor...")
    
    # 1. Metin
    writer = PostWriter()
    post_text = writer.write_weekly_news_post("Test araştırması: AI ajanı uçtan uca test prensibini uyguluyor.")
    print("📋 Metin Üretildi:", post_text[:100] + "...")
    
    # 2. Görsel
    img_gen = ImageGenerator()
    image_path = img_gen.generate_post_image(post_text)
    if not image_path:
        raise RuntimeError("Görsel üretilemedi! HATA.")
    print("🖼️ Görsel Üretildi:", image_path)
    
    # 3. Paylaş
    publisher = LinkedInPublisher()
    post_urn = publisher.create_text_image_post(text=post_text, image_path=image_path)
    print("🚀 LinkedIn'e Paylaşıldı! URN:", post_urn)
    
    # URL oluşturma
    try:
        url = f"https://www.linkedin.com/feed/update/{post_urn}/"
        print("\n✅ TEST BAŞARILI! Görmek için tıklayın:")
        print(url)
    except Exception as e:
        print("URL oluşturulamadı ama paylaşıldı:", post_urn)

if __name__ == "__main__":
    test_pipeline()
