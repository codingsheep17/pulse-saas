import reflex as rx
from supabase import create_client
from dotenv import load_dotenv
import os
import time

#initializing the essentials
load_dotenv()

supbase: Client = create_client(os.getenv("PUBLIC_SUPABASE_URL"), os.getenv("PUBLIC_SUPABASE_PUBLISHABLE_KEY"))

response = supbase.auth.sign_up({
    "email":"codingsheep17@gmail.com",
    "password":"haseeb19."
})