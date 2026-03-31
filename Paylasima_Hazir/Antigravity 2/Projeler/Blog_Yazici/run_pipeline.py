#!/usr/bin/env python3
"""
Blog_Yazici Otomatik Pipeline Scripti
Bu script tüm blog yazma adımlarını sırayla çalıştırır ve hata yönetimini yapar.
Kullanım: python run_pipeline.py <video_klasoru>
"""

import os
import sys
import subprocess

def run_step(step_name, command_args):
    print(f"\n============================================================")
    print(f"🚀 PIPELINE ADIMI BAŞLIYOR: {step_name}")
    print(f"============================================================")
    
    try:
        # Popen yerine run kullanıyoruz, çıktıyı doğrudan stdout'a basar.
        result = subprocess.run(
            command_args, 
            check=True,
            text=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ HATA: '{step_name}' aşamasında bir sorun oluştu! (Exit Code: {e.returncode})")
        print("Pipeline durduruldu.")
        sys.exit(1)

def main():
    # Varsayılan klasör 'typeless5'
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "./Projeler/Blog_Yazici/typeless5"
    target_dir = os.path.abspath(target_dir)

    # Ortam değişkenleri içindeki yeni yaratılan virtual environment'ı kullan
    python_bin = os.path.join(os.path.dirname(os.path.abspath(__file__)), "env", "bin", "python3")

    print(f"Hedef Klasör: {target_dir}")
    print("Sırayla çalıştırılacak araçlar:")
    print(" 1. extract_frames.py")
    print(" 2. vision_analyzer.py")
    print(" 3. annotate_v3.py")
    print(" 4. generate_blog.py")
    
    # 1. Frame Çıkarma
    if os.path.isfile(target_dir):
        video_path = target_dir
        target_dir = os.path.splitext(video_path)[0]
        frames_dir = os.path.join(target_dir, "frames")
        run_step(
            "Adım 1: extract_frames.py",
            [python_bin, "extract_frames.py", video_path, frames_dir]
        )
    else:
        frames_dir = os.path.join(target_dir, "frames")
        print(f"\nAdım 1 Atlandı: {target_dir} bir video dosyası değil. Mevcut '{frames_dir}' klasörü kullanılacak.")
    
    # 2. Vision Analysis (Groq ile frame değerlendirmesi)
    run_step(
        "Adım 2: vision_analyzer.py",
        [python_bin, "vision_analyzer.py", frames_dir]
    )
    
    # 3. Annotation and Self-Review
    run_step(
        "Adım 3: annotate_v3.py",
        [python_bin, "annotate_v3.py", target_dir]
    )
    
    # 4. Blog Generation (Gemini 2.5 Flash ile)
    run_step(
        "Adım 4: generate_blog.py",
        [python_bin, "generate_blog.py", target_dir]
    )
    
    print("\n✅ TÜM PIPELINE BAŞARIYLA TAMAMLANDI!")

if __name__ == "__main__":
    main()
