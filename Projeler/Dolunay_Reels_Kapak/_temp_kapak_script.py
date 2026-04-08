import random, os
from autonomous_cover_agent import run_autonomous_generation, generate_three_themes

cutout_dir = 'assets/cutouts'
cutouts = [f for f in os.listdir(cutout_dir) if f.endswith('.png')]

script_text = """D1: bu bayram çok yedim 4 kilo almışım ( o sırada hamburger vb. kilo aldıran bir şeyi yer) 
D2: o yediğin şey kaç kalori haberin var mı peki ( ardından hamburgerin fotoğrafını çeker )
D1: kaç?
D2: yuh 1000 kalori
D1: nasıl ya
D2: bak bu uygulama fotoğrafını çektiğim yemeğin bana kalorisini söylüyor
D1: çok iyimiş nerden buldun ?
D2: kendim yaptım
D1: nasıl ya ?
D2: Evet, hatta bunu App Store’da yayınlamayı bile düşünüyorum..
D1: Ya tamam da nasıl?
D2: blinke girip bana bir beslenme uygulaması yapmasını istedim 1 dakika içinde hazırladı
D1: abi benim de bi fikrim var aslında neydi adı
INSTAGRAM CLOSING
D2: yoruma fikir yaz sana gönderiyim
TIKTOK/SHORTS CLOSING
D2: BLINK kaydet lazım olur"""

themes = generate_three_themes('Blink Yemeğin Kalorisini Öğren', script_text)

for t_idx, theme in enumerate(themes, 1):
    cover_text = theme['cover_text']
    scene_desc = theme['scene_description']
    theme_name = theme['theme_name']
    print(f"\nTema {t_idx}: {theme_name} → {cover_text}")
    
    for v_idx in range(1, 3):
        cutout = os.path.join(cutout_dir, random.choice(cutouts))
        output = f'outputs/kapak_T{t_idx}_{theme_name}_V{v_idx}.png'
        run_autonomous_generation(
            local_person_image_path=cutout,
            video_topic='Blink AI Fotoğraftan Kalori Hesaplama',
            main_text=cover_text,
            output_path=output,
            max_retries=2,
            variant_index=v_idx,
            script_text=script_text,
            scene_description=scene_desc
        )
        print(f"  Varyasyon {v_idx} tamamlandı: {output}")
