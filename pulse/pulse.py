import reflex as rx
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_PUBLISHABLE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY)

class AuthState(rx.State):
    """State management for user authentication (Login & Signup)."""
    email: str = ""
    password: str = ""
    error_message: str = ""
    success_message: str = ""

    # Explicit setters to prevent compiler AttributeErrors
    def set_email(self, email_input: str):
        self.email = email_input

    def set_password(self, password_input: str):
        self.password = password_input

    @rx.event
    def handle_signup(self):
        try:
            response = supabase.auth.sign_up({"email": self.email, "password": self.password})
            self.success_message = "Registration successful! Check your email for confirmation."
            self.error_message = ""
        except Exception as e:
            self.error_message = str(e)
            self.success_message = ""

    @rx.event
    def handle_login(self):
        try:
            response = supabase.auth.sign_in_with_password({"email": self.email, "password": self.password})
            self.success_message = "Login successful! Redirecting..."
            self.error_message = ""
        except Exception as e:
            self.error_message = str(e)
            self.success_message = ""

def index() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.heading("Pulse : Access Portal", font_size="2em", color="#0f172a"),
            rx.text("Secure Infrastructure Intelligence", color="#64748b", margin_bottom="20px"),
            
            rx.input(
                placeholder="name@company.com", 
                on_change=AuthState.set_email,
                width="300px",
                background_color="#ffffff",
                color="#0f172a"
            ),
            rx.input(
                type="password", 
                placeholder="********", 
                on_change=AuthState.set_password,
                width="300px",
                background_color="#ffffff",
                color="#0f172a"
            ),
            
            rx.hstack(
                rx.button("Sign In", on_click=AuthState.handle_login, color_scheme="blue", width="140px"),
                rx.button("Register", on_click=AuthState.handle_signup, variant="outline", width="140px"),
                spacing="4",
            ),
            
            rx.cond(
                AuthState.error_message != "",
                rx.text(AuthState.error_message, color="red", font_size="0.9em")
            ),
            rx.cond(
                AuthState.success_message != "",
                rx.text(AuthState.success_message, color="green", font_size="0.9em")
            ),
            
            background_color="#f8fafc",
            padding="40px",
            border_radius="12px",
            border="1px solid #e2e8f0",
            box_shadow="lg",
            align_items="center",
        ),
        height="100vh",
        background_color="#0f172a",
    )

app = rx.App()
app.add_page(index, title="Pulse | Login")