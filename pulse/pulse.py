import reflex as rx
from supabase import create_client
from dotenv import load_dotenv
import os
import time

#loading the envs
load_dotenv()

#fetching url and key
PUBLIC_SUPABASE_URL = os.getenv("PUBLIC_SUPABASE_URL")
PUBLIC_SUPABASE_PUBLISHABLE_KEY = os.getenv("PUBLIC_SUPABASE_PUBLISHABLE_KEY")
TURNSTILE_SITE_KEY=os.getenv("TURNSTILE_SITE_KEY")

#making client
supabase = create_client(
    PUBLIC_SUPABASE_URL,
    PUBLIC_SUPABASE_PUBLISHABLE_KEY
)
