import reflex as rx
from supabase import create_client
from dotenv import load_dotenv
import os
import time

# --- 1. ADD THIS RIGHT BELOW YOUR IMPORTS ---

# Pulse Global Colors
BG = "#0D1110"
NAV_BG = "#151B18"
CARD_BG = "#1C2420"
GREEN = "#B7E36B"
YELLOW = "#F2D16B"
TEXT = "#F3F5F2"
MUTED = "#A8B0AC"
BORDER = "#303A35"

# Global App Style
PULSE_STYLE = {
    "background_color": BG,
    "color": TEXT,
    "font_family": "system-ui, -apple-system, sans-serif",
    # This makes highlighted text look like your green accent!
    "::selection": {
        "background_color": GREEN,
        "color": BG,
    }
}

# (Keep your existing AuthState class and imports exactly as they are)

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

#Session Dealing logic comes here
class AuthState(rx.State):
    email: str = ""
    password: str = ""

    message: str = ""
    message_type: str = ""   # "success" or "error"
    
    #captcha vars
    turnstile_token: str = ""
    is_authenticated: bool = False
    last_signup_attempt: float = 0.0
    
    @rx.event
    def set_email(self, value: str):
        self.email = value

    @rx.event
    def set_password(self, value: str):
        self.password = value
    
    @rx.event
    def check_auth(self):
        try:
            user = supabase.auth.get_user()
            if user is None:
                self.is_authenticated = False
                return rx.redirect("/")
            self.is_authenticated = True
        except Exception:
            self.is_authenticated = False
            return rx.redirect("/")

    #captcha event
    @rx.event
    def set_turnstile_token(self, token: str):
        self.turnstile_token = token
        
    @rx.event
    def login(self, token: str):
        
        if not token:
            self.message = "Please complete the CAPTCHA."
            self.message_type = "error"
            return
            
        if not self.email or not self.password:
            self.message = "Please enter your email and password."
            self.message_type = "error"
            return

        try:
            response = supabase.auth.sign_in_with_password({
                "email": self.email,
                "password": self.password,
            })

            self.is_authenticated = True
            self.message = "Login successful!"
            self.message_type = "success"

            return rx.redirect("/home")

        except Exception:
            self.is_authenticated = False
            self.message = "Incorrect email or password."
            self.message_type = "error"

    @rx.event
    def signup(self):
        #cooldown Timer (60 seconds)
        current_time = time.time()
        if current_time - self.last_signup_attempt < 60:
            remaining = int(60 - (current_time - self.last_signup_attempt))
            self.message = f"Please wait {remaining} seconds before requesting another email."
            self.message_type = "error"
            return

        if not self.email or not self.password:
            self.message = "Please enter your email and password."
            self.message_type = "error"
            return

        if len(self.password) < 6:
            self.message = "Password must be at least 6 characters."
            self.message_type = "error"
            return

        try:
            #update timestamp right before making the network request
            self.last_signup_attempt = current_time
            response = supabase.auth.sign_up({
                "email": self.email,
                "password": self.password,
            })

            #check for existing accounts (Supabase empty identities array check)
            if response.user and getattr(response.user, "identities", None) == []:
                self.message = "This email is already registered. Please log in."
                self.message_type = "error"
            elif response.user and response.session is None:
                self.message = "Registration successful! Check your email to verify your account."
                self.message_type = "success"
            else:
                self.message = "Account created successfully!"
                self.message_type = "success"

        except Exception as e:
            error_msg = str(e).lower()
            if "rate limit" in error_msg or "too many requests" in error_msg:
                self.message = "Too many requests. Please wait a moment before trying again."
            else:
                self.message = str(e)
            self.message_type = "error"

    @rx.event
    def logout(self):
        try:
            supabase.auth.sign_out()

            # 1. Clear backend state completely
            self.is_authenticated = False
            self.message = ""
            self.message_type = ""
            self.email = ""
            self.password = ""
            self.turnstile_token = ""

            # 2. Tell Reflex to do TWO things simultaneously: clear the JS token AND redirect
            return [
                rx.call_script("window.turnstileToken = null;"),
                rx.redirect("/")
            ]

        except Exception as e:
            self.message = "Logout failed."
            self.message_type = "error"


    def google_login(self):
        try:
            response = supabase.auth.sign_in_with_oauth({
                "provider": "google"
            })

        except Exception as e:
            self.message = "Google login failed."
            self.message_type = "error"
    



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