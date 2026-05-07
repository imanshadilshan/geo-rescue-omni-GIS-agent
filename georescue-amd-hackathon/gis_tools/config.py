"""Project configuration."""
from dotenv import load_dotenv 
import os 
 
load_dotenv() 
 
CLIENT_ID = os.getenv("SENTINEL_CLIENT_ID") 
CLIENT_SECRET = os.getenv("SENTINEL_CLIENT_SECRET")