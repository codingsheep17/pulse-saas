import reflex as rx
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_PUBLISHABLE_KEY = os.getenv("SUPABASE_PUBLISHABLE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY)

class AuthState(rx.State):
    """State management for user authentication."""
    email: str = ""
    password: str = ""
    error_message: str = ""
    success_message: str = ""

    def set_email(self, email_input: str):
        self.email = email_input.strip()

    def set_password(self, password_input: str):
        self.password = password_input

    def reset_messages(self):
        self.error_message = ""
        self.success_message = ""

    @rx.event
    def handle_google_login(self):
        self.reset_messages()
        try:
            response = supabase.auth.sign_in_with_oauth({"provider": "google"})
            return rx.redirect(response.url)
        except Exception:
            self.error_message = "Google login unavailable."

    @rx.event
    def handle_signup(self):
        self.reset_messages()
        if not self.email or not self.password:
            self.error_message = "Email and password required."
            return
        try:
            response = supabase.auth.sign_up({"email": self.email, "password": self.password})
            if response.user and getattr(response.user, "identities", None) == []:
                self.error_message = "Account exists. Please sign in."
            else:
                self.success_message = "Account created. Please sign in."
        except Exception:
            self.error_message = "Registration failed. Check credentials."

    @rx.event
    def handle_login(self):
        self.reset_messages()
        if not self.email or not self.password:
            self.error_message = "Email and password required."
            return
        try:
            response = supabase.auth.sign_in_with_password({"email": self.email, "password": self.password})
            if response.user:
                self.success_message = "Authenticated. Redirecting..."
        except Exception:
            self.error_message = "Invalid credentials."

def index() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.heading("Pulse", font_size="2.5em", color="#ffffff", font_weight="900", letter_spacing="-1px"),
            rx.text("Infrastructure Intelligence", color="#a1a1aa", margin_bottom="30px"),
            
            rx.button(
                "Continue with Google", 
                on_click=AuthState.handle_google_login,
                width="100%", 
                background_color="#ffffff", 
                color="#09090b",
                font_weight="bold",
                border_radius="8px",
                padding="20px",
                _hover={"background_color": "#e4e4e7"}
            ),
            
            rx.hstack(
                rx.divider(border_color="#3f3f46"),
                rx.text("OR", color="#71717a", font_size="0.8em", font_weight="bold"),
                rx.divider(border_color="#3f3f46"),
                width="100%",
                margin_top="25px",
                margin_bottom="25px",
                align_items="center"
            ),
            
            rx.input(
                placeholder="Email address", 
                on_change=AuthState.set_email,
                width="100%",
                background_color="#27272a",
                border="1px solid #3f3f46",
                color="#ffffff",
                border_radius="8px",
                padding="10px",
                margin_bottom="10px",
                _placeholder={"color": "#a1a1aa"},
                _focus={"border_color": "#38bdf8", "box_shadow": "0 0 0 1px #38bdf8"}
            ),
            rx.input(
                type="password", 
                placeholder="Password", 
                on_change=AuthState.set_password,
                width="100%",
                background_color="#27272a",
                border="1px solid #3f3f46",
                color="#ffffff",
                border_radius="8px",
                padding="10px",
                _placeholder={"color": "#a1a1aa"},
                _focus={"border_color": "#38bdf8", "box_shadow": "0 0 0 1px #38bdf8"}
            ),
            
            rx.hstack(
                rx.button("Continue", on_click=AuthState.handle_login, background_color="#38bdf8", color="#0f172a", font_weight="bold", flex="1", border_radius="8px", _hover={"background_color": "#7dd3fc"}),
                rx.button("Sign Up", on_click=AuthState.handle_signup, variant="outline", border_color="#3f3f46", color="#ffffff", flex="1", border_radius="8px", _hover={"background_color": "#27272a"}),
                spacing="4",
                width="100%",
                margin_top="15px"
            ),
            
            rx.cond(
                AuthState.error_message != "",
                rx.text(AuthState.error_message, color="#ef4444", font_size="0.9em", font_weight="bold", margin_top="15px")
            ),
            rx.cond(
                AuthState.success_message != "",
                rx.text(AuthState.success_message, color="#22c55e", font_size="0.9em", font_weight="bold", margin_top="15px")
            ),
            
            background_color="#18181b",
            padding="50px 40px",
            border_radius="16px",
            border="1px solid #27272a",
            box_shadow="0 25px 50px -12px rgba(0, 0, 0, 0.8)",
            align_items="center",
            width="100%",
            max_width="400px", 
        ),
        width="100%",
        height="100vh",
        background_color="#09090b",
        padding="20px", 
    )

app = rx.App()
app.add_page(index, title="Pulse | Access Portal")