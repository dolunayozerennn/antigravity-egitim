#!/bin/bash
curl -s -X POST 'https://xsmhuhrfgthrhlakcltm.supabase.co/functions/v1/reklam-pipeline?action=start-multi' \
  -H 'Content-Type: application/json' \
  -d '{
    "imageUrl": "https://lh3.googleusercontent.com/d/1FkLv4wy89T-Wb2MNJrE23ORJyPk4GKT4",
    "scenes": [
      {
        "name": "unboxing",
        "duration": 5,
        "prompt": "Close-up handheld smartphone camera POV. A woman elegant hand with red manicure reaches into a sleek matte black shoebox and lifts out a pair of glossy red patent leather stiletto heels. Natural soft window lighting from the right, warm golden tones. The camera slightly shakes like authentic UGC social media content. She turns the shoe slowly, admiring the glossy finish. Bedroom setting with neutral minimalist aesthetic background. Authentic influencer video feel. No dialogue, no speaking, no text overlay."
      },
      {
        "name": "detail_styling",
        "duration": 5,
        "prompt": "Ultra close-up macro shot of glossy red patent leather stiletto heel texture, light dancing across the mirror-like surface. Camera slowly pulls back with handheld shake to reveal the shoes placed artfully next to a chic black cocktail dress on a clean white marble surface. Quick energetic camera pan. Natural daylight from a large window, Instagram-aesthetic warm color grading. Flat-lay transitioning to styled shot. Authentic influencer content feel, TikTok UGC style. No dialogue, no speaking, no text overlay."
      },
      {
        "name": "power_walk",
        "duration": 5,
        "prompt": "Dynamic low angle tracking shot following glossy red patent leather stiletto heels walking confidently on polished white marble floor. Camera at ground level captures each powerful step with slight handheld shake. The heels gleam and reflect warm ambient light with each stride. Energetic pace, the walk builds momentum then ends with a confident stop and slight turn. Modern luxury hotel lobby setting with blurred elegant background. Empowering mood, influencer-style vertical video. No dialogue, no speaking, no text overlay."
      }
    ]
  }'
