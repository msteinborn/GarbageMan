import httpx
import time
import sys

def wait_for_bus(url, retries=5):
    print(f"Checking system bus at {url}...")
    for i in range(retries):
        try:
            response = httpx.get(url)
            if response.status_code == 200:
                print("Bus Status: READY")
                return True
        except httpx.RequestError:
            print(f"Bus Status: BUSY (Attempt {i+1}/{retries})")
            time.sleep(2)
    return False

def main():
        URL = "http://tools:8000"   
        print("--- Control Unit (Brain) Started ---")
        try:
            r = httpx.get(f"{URL}/hello")
            print(f"Signal received from Tool Server: {r.json()}")
        except Exception as e:
            print(f"Bus Error: {e}")

       
if __name__ == "__main__":
    if not wait_for_bus("http://tools:8000/health"):
        print("CRITICAL ERROR: System Bus Timeout. Exiting.")
        sys.exit(1)
    
    print("--- Starting Agent Logic ---")
    main()
