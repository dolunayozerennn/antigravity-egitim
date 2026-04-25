import sys
import os
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv("../../_knowledge/credentials/master.env")

from core.linkedin_publisher import LinkedInPublisher

def test_upload():
    pub = LinkedInPublisher()
    
    # 1. Initialize Upload
    urn = pub._initialize_upload(1024)
    if not urn:
        print("Failed to initialize upload.")
        return
        
    print(f"Initialized URN: {urn}")
    
    # 2. Check Status
    pub._finalize_upload(urn)

if __name__ == "__main__":
    test_upload()
