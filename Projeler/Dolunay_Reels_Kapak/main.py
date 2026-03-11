import os
import random
from notion_service import get_ready_videos
from autonomous_cover_agent import run_autonomous_generation, generate_cover_text_and_scene
from drive_service import upload_cover_to_drive, check_covers_exist

def process_ready_videos():
    print("=== Starting Auto Cover Generation Pipeline ===")
    videos = get_ready_videos()
    
    if not videos:
        print("No videos found with 'Çekildi - Edit YOK' status.")
        return

    # Create outputs folder if not exists
    os.makedirs("outputs", exist_ok=True)
    
    # Get available pre-processed photos
    cutout_dir = "outputs/cutouts"
    if not os.path.exists(cutout_dir):
        print(f"Error: {cutout_dir} directory not found. Run process_all_raw.py first.")
        return
        
    available_cutouts = [f for f in os.listdir(cutout_dir) if f.lower().endswith(('png', 'jpg', 'jpeg'))]
    if not available_cutouts:
        print(f"Error: No image files found in {cutout_dir}.")
        return

    for video in videos:
        print(f"\n--- Processing Video: {video['name']} ---")
        
        drive_url = video.get('drive_url')
        if not drive_url:
            print(f"Skipping {video['name']}: No Drive URL found in Notion properties.")
            continue
            
        # Check if covers already exist in the Drive folder
        if check_covers_exist(drive_url):
            print(f"Skipping {video['name']}: Covers already exist in Drive folder.")
            continue
        
        # Generate cover text AND scene description together for consistency
        topic = video['name']
        script_content = video.get('script_text', '')
        text_result = generate_cover_text_and_scene(topic, script_content)
        main_text = text_result.get("cover_text", topic.upper())
        scene_description = text_result.get("scene_description", "")
        
        print(f"  Cover Text: {main_text}")
        print(f"  Scene: {scene_description}")
        
        # We will generate 3 variants
        for variant_index in range(1, 4):
            print(f"\n>> Generating Variant {variant_index} for {video['name']}")
            
            # Select a random cutout
            cutout_name = random.choice(available_cutouts)
            cutout_path = os.path.join(cutout_dir, cutout_name)
            
            print(f"Using cached cutout: {cutout_path}")
            
            # Run Autonomous Generation Loop
            safe_video_name = "".join([c for c in video['name'] if c.isalpha() or c.isdigit() or c==' ']).rstrip()
            final_cover_filename = f"{safe_video_name} KAPAK {variant_index}.png"
            final_cover_path = os.path.join("outputs", final_cover_filename)
            print(f"Generating AI Cover Variant {variant_index} (Max 2 Attempts)...")
            
            success = run_autonomous_generation(
                local_person_image_path=cutout_path,
                video_topic=topic,
                main_text=main_text,
                output_path=final_cover_path,
                max_retries=2,
                variant_index=variant_index,
                script_text=script_content,
                scene_description=scene_description
            )
            
            if not success:
                 print(f"Failed to generate variant {variant_index}. Skipping to next variant.")
                 continue
                 
            # Upload to Google Drive
            print("Uploading to Google Drive...")
            if drive_url:
                upload_cover_to_drive(final_cover_path, drive_url, file_name=f"Kapak {variant_index}.png")
            else:
                print("No Google Drive URL found for this video.")
            
    print("\n=== Pipeline Execution Completed ===")

if __name__ == "__main__":
    process_ready_videos()
