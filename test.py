import os
from dotenv import load_dotenv

load_dotenv()

ip = os.getenv("DIRECT_IP")

print(ip)
