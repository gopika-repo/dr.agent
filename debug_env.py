import os
from dotenv import load_dotenv

# Try to load .env
success = load_dotenv()
print(f"load_dotenv() success: {success}")

token = os.getenv("GITHUB_TOKEN")
if token:
    print(f"Token length: {len(token)}")
    print(f"Token starts with: {token[:4]}")
    print(f"Token ends with: {token[-4:]}")
    print(f"Raw token repr: {repr(token)}")
else:
    print("Token not found in environment")
