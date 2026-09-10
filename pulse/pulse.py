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

#app and its paths
app = rx.App(
    head_components=[
        rx.script(src="https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit", async_=True, defer=True)
    ]
)
app.add_page(index, route="/", on_load=rx.call_script("setTimeout(renderCaptcha, 200);"))
app.add_page(home, route="/home", on_load=AuthState.check_auth,)
app.add_page(about,route="/about",on_load=AuthState.check_auth,)
app.add_page(services,route="/services",on_load=AuthState.check_auth,)
app.add_page(contact,route="/contact",on_load=AuthState.check_auth,)