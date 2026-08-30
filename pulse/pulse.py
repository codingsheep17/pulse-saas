from supabase import create_client, Client
from dotenv import load_dotenv
import os

#initializing the essentials
load_dotenv()

supbase: Client = create_client(os.getenv("PUBLIC_SUPABASE_URL"), os.getenv("PUBLIC_SUPABASE_PUBLISHABLE_KEY"))
