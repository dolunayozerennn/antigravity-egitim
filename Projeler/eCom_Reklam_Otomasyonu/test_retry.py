import requests
from utils.retry import retry_api_call
import sys

class MockResponse:
    def __init__(self, status_code):
        self.status_code = status_code
        self.headers = {}

class MockHTTPError(requests.exceptions.HTTPError):
    def __init__(self, status_code):
        self.response = MockResponse(status_code)

call_count = 0

@retry_api_call(max_retries=3, base_delay=0.1)
def failing_api_call():
    global call_count
    call_count += 1
    if call_count <= 2:
        print(f"Attempt {call_count}: Raising 512")
        raise MockHTTPError(512)
    print(f"Attempt {call_count}: Success!")
    return "OK"

try:
    res = failing_api_call()
    if res == "OK" and call_count == 3:
        print("Retry mechanism test PASSED")
    else:
        print("Retry mechanism test FAILED")
        sys.exit(1)
except Exception as e:
    print(f"Retry mechanism test FAILED with exception: {e}")
    sys.exit(1)
