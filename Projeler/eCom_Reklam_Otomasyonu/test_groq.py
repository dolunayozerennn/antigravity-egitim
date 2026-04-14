import os
import sys

# Yollari ekle
sys.path.append(os.path.join(os.getcwd(), 'services'))

# Oku
with open('../../_knowledge/credentials/master.env') as f:
    for line in f:
        if line.startswith('GROQ_API_KEY='):
            os.environ['GROQ_API_KEY'] = line.split('=', 1)[1].strip()
        if line.startswith('GROQ_BASE_URL='):
            os.environ['GROQ_BASE_URL'] = line.split('=', 1)[1].strip()

import openai
client = openai.OpenAI(
    api_key=os.environ['GROQ_API_KEY'],
    base_url=os.environ['GROQ_BASE_URL']
)

try:
    # Test vision query with explicit names
    response = client.chat.completions.create(
        model="llama-3.2-11b-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What's in this image? Please describe it shortly."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wis-carls_srgb_7578.jpg/2560px-Gfp-wis-carls_srgb_7578.jpg",
                        },
                    },
                ],
            }
        ],
    )
    print("11b Response:")
    print(response.choices[0].message.content)
except Exception as e:
    print(f"Error 11b: {e}")

try:
    # Test vision query with explicit names
    response = client.chat.completions.create(
        model="llama-3.2-90b-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What's in this image? Please describe it shortly."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wis-carls_srgb_7578.jpg/2560px-Gfp-wis-carls_srgb_7578.jpg",
                        },
                    },
                ],
            }
        ],
    )
    print("90b Response:")
    print(response.choices[0].message.content)
except Exception as e:
    print(f"Error 90b: {e}")
