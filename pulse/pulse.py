import reflex as rx
from supabase import create_client
from dotenv import load_dotenv
import os
import time


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
    
# NAVBAR
# ===============================================================================

def navbar():

    return rx.vstack(

        rx.hstack(

            rx.heading(
                "sheep",
                size="6",
                color=GREEN,
            ),

            rx.spacer(),

            rx.hstack(

                rx.link(
                    "Home",
                    href="/home",
                    color=TEXT,
                ),

                rx.link(
                    "About",
                    href="/about",
                    color=TEXT,
                ),

                rx.link(
                    "Services",
                    href="/services",
                    color=TEXT,
                ),

                rx.link(
                    "Contact",
                    href="/contact",
                    color=TEXT,
                ),
                rx.cond(
                    AuthState.is_authenticated,
                    rx.button(
                        "Logout",
                        width="20%",
                        background=GREEN,
                        color=BG,
                        on_click=AuthState.logout,
                    ),
                ),

                spacing="6",
            ),

            width="100%",
            align="center",

        ),

        # Green bottom line
        rx.box(
            width="100%",
            height="3px",
            background=GREEN,
        ),

        width="100%",
        background=NAV_BG,
        padding="20px 40px 0 40px",
    )

#================================================================================
# AUTH CARD
# ========================
def auth_card():

    return rx.box(

        rx.vstack(

            rx.heading(
                "Welcome to sheep",
                size="8",
                color=TEXT,
                text_align="center",
            ),

            rx.text(
                "Login or SignUp",
                color=MUTED,
                text_align="center",
            ),

            rx.input(
                placeholder="Email",
                type="email",
                width="100%",
                background="#252D29",
                border_color=BORDER,
                value=AuthState.email,
                on_change=AuthState.set_email,
            ),

            rx.input(
                placeholder="Password",
                type="password",
                width="100%",
                background="#252D29",
                border_color=BORDER,
                value=AuthState.password,
                on_change=AuthState.set_password,
            ),
            rx.cond(
            AuthState.message != "",
            rx.text(
                AuthState.message,
                color=rx.cond(
                    AuthState.message_type == "success",
                    GREEN,
                    YELLOW,
                    ),
                text_align="center",
                ),
            ),
            #adding the captcha here 
            
            #Load the official Cloudflare library securely
            rx.script(src="https://challenges.cloudflare.com/turnstile/v0/api.js", async_=True, defer=True),
            
            #Define the global success callback so Cloudflare can save the token
            rx.script(
                f"""
                function renderCaptcha() {{
                    // Only run if Cloudflare is loaded and our div exists
                    if (window.turnstile && document.getElementById('my-captcha-box')) {{
                        
                        // GARBAGE COLLECTION: Destroy the old ghost widget if it exists
                        if (window.pulseWidgetId !== undefined) {{
                            try {{ window.turnstile.remove(window.pulseWidgetId); }} catch(e) {{}}
                        }}
                        
                        // Render a fresh widget and save its unique ID
                        window.pulseWidgetId = window.turnstile.render('#my-captcha-box', {{
                            sitekey: '{TURNSTILE_SITE_KEY}',
                            theme: 'dark',
                            callback: function(token) {{
                                window.turnstileToken = token;
                                console.log("CAPTCHA Passed! Token saved.");
                            }}
                        }});
                    }}
                }}
                """
            ),
            
            # The actual container
            rx.html('<div id="my-captcha-box"></div>'),

            #Cloudflare automatically finds this div and renders the CAPTCHA
            rx.html(
                f"""
                <div class="cf-turnstile" 
                     data-sitekey="{TURNSTILE_SITE_KEY}" 
                     data-callback="onTurnstileSuccess" 
                     data-theme="dark">
                </div>
                """
            ),
            
            rx.button(
                "Login",
                width="100%",
                background=GREEN,
                color=BG,
                on_click=rx.call_script(
                "window.turnstileToken || ''",
                callback=AuthState.login,
                ),
            ),

            rx.divider(
                color=BORDER,
            ),

            rx.button(
                "Continue with Google",
                width="100%",
                variant="outline",
                border_color=YELLOW,
                color=YELLOW,
                on_click=AuthState.google_login,
            ),

            rx.text(
                "Don't have an account?",
                color=MUTED,
            ),

            rx.button(
                "SignUp",
                width="100%",
                variant="outline",
                border_color=GREEN,
                color=GREEN,
                on_click=AuthState.signup,
            ),

            spacing="5",
            width="100%",

        ),

        width="420px",
        padding="38px",

        background=CARD_BG,

        border="1px solid",
        border_color=BORDER,

        border_radius="20px",

        box_shadow="0 20px 60px rgba(0, 0, 0, 0.35)",
    )

#================================================================================
# FOOTER
# =========================

def footer():

    return rx.vstack(

        rx.box(
            width="100%",
            height="3px",
            background=GREEN,
        ),

        rx.box(

            # LEFT
            rx.text(
                "© sheep",
                color=GREEN,
                position="absolute",
                left="40px",
                top="50%",
                transform="translateY(calc(-50% - 7.5px))",
            ),

            # CENTER
            rx.hstack(

                rx.link(
                    rx.image(
                        src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg",
                        width="22px",
                        height="22px",
                    ),
                    href="https://www.linkedin.com/in/syedhaseebshah19/",
                    is_external=True,
                ),

                rx.link(
                    rx.image(
                        src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/github/github-original.svg",
                        width="22px",
                        height="22px",
                        style={"filter": "invert(1)"},
                    ),
                    href="https://github.com/codingsheep17",
                    is_external=True,
                ),

                rx.link(
                    rx.image(
                        src="https://upload.wikimedia.org/wikipedia/commons/a/a0/YouTube_social_red_circle_%282017%29.svg",
                        width="22px",
                        height="22px",
                    ),
                    href="https://www.youtube.com/@codingsheep17",
                    is_external=True,
                ),

                spacing="6",
                position="absolute",
                left="50%",
                top="50%",
                transform="translate(-50%, calc(-50% - 6px))",
            ),

            # RIGHT
            rx.text(
                "codingsheep17@gmail.com",
                color=GREEN,
                position="absolute",
                right="40px",
                top="50%",
                transform="translateY(calc(-50% - 7.5px))",
            ),

            width="100%",
            height="35px",
            position="relative",
        ),

        width="100%",
        background=NAV_BG,
    )
    
#=================================================================================
# ABOUT
def about():

    return rx.vstack(

        navbar(),

        rx.center(
            rx.heading(
                "About Us",
                size="8",
                color=GREEN,
            ),
            flex="1",
        ),

        footer(),

        min_height="100vh",
        background=BG,
    )

# SERVICES
# ================================================================================

def services():

    return rx.vstack(

        navbar(),

        rx.center(
            rx.heading(
                "Our Services",
                size="8",
                color=GREEN,
            ),
            flex="1",
        ),

        footer(),

        min_height="100vh",
        background=BG,
    )
    
# CONTACT
# ================================================================================
def contact():

    return rx.vstack(

        navbar(),

        rx.center(
            rx.heading(
                "Contact Us",
                size="8",
                color=GREEN,
            ),
            flex="1",
        ),

        footer(),

        min_height="100vh",
        background=BG,
    )

# LANDING PAGE COMPONENTS
# ===============================================================================

def landing_hero():
    return rx.vstack(
        # Huge PULSE heading
        rx.heading(
            "PULSE", 
            font_size="6em", 
            font_weight="900", 
            color=TEXT,
            letter_spacing="-2px"
        ),
        
        # Summary text
        rx.text(
            "shortest summary goes here", 
            size="6", 
            color=TEXT, 
            font_weight="bold",
            margin_top="20px"
        ),
        
        # Blueprint Box Styling
        background=CARD_BG,
        padding="100px",
        border_radius="30px",
        width="80%",
        max_width="1000px",
        align_items="center",
        justify_content="center",
        border=f"1px solid {BORDER}",
        box_shadow="0 20px 60px rgba(0, 0, 0, 0.35)",
        margin_bottom="40px",
    )
    
# LANDING PAGE COMPONENTS
# ===============================================================================
def feature_card(title: str, description: str):
    """Creates a stylized card with a hover animation."""
    return rx.box(
        rx.vstack(
            rx.heading(title, size="6", color=GREEN, margin_bottom="10px"),
            rx.text(description, color=MUTED, line_height="1.6"),
            align_items="start",
        ),
        background=CARD_BG,
        padding="40px",
        border_radius="20px",
        border=f"1px solid {BORDER}",
        width=["100%", "100%", "45%"],  # Full width on mobile, 45% on desktop
        transition="all 0.3s ease",
        _hover={
            "transform": "translateY(-10px)",
            "border_color": GREEN,
            "box_shadow": "0 10px 30px rgba(183, 227, 107, 0.15)",
        }
    )

def feature_row(text_title: str, text_desc: str, card_title: str, card_desc: str, card_on_left: bool = False):
    """Creates a zigzag row with text on one side and a card on the other."""
    text_section = rx.vstack(
        rx.heading(text_title, size="7", color=TEXT, margin_bottom="10px"),
        rx.text(text_desc, color=MUTED, size="4", line_height="1.6"),
        align_items="start",
        width=["100%", "100%", "45%"],
        padding_y=["20px", "20px", "0px"], # Adds spacing on mobile
    )
    
    card_section = feature_card(card_title, card_desc)
    
    # Determine the order based on the card_on_left flag
    items = [card_section, text_section] if card_on_left else [text_section, card_section]
    
    return rx.flex(
        *items,
        direction=["column", "column", "row"], # Stacks vertically on mobile, horizontally on desktop
        justify_content="space-between",
        align_items="center",
        width="100%",
        max_width="1000px",
        margin_bottom="100px",
    )
    
def landing_features():
    """Assembles all the features in the requested zigzag pattern."""
    return rx.vstack(
        # 1. Right Card: RAM
        feature_row(
            "Memory Optimization", 
            "Track memory allocation in real-time. Pulse monitors active processes to prevent out-of-memory crashes before they happen.",
            "RAM Usage", 
            "Live monitoring of volatile memory consumption across all your infrastructure.",
            card_on_left=False
        ),
        # 2. Left Card: CPU
        feature_row(
            "Processing Power",
            "Analyze thread loads and processor bottlenecks. Identify rogue processes consuming too many cycles.",
            "CPU Usage",
            "Per-core performance metrics and historical load analysis.",
            card_on_left=True
        ),
        # 3. Right Card: GPU
        feature_row(
            "Hardware Acceleration",
            "Keep an eye on compute-heavy workloads. Perfect for AI and machine learning infrastructure monitoring.",
            "GPU Usage",
            "VRAM allocation, core temperature, and compute utilization tracking.",
            card_on_left=False
        ),
        # 4. Left Card: Network
        feature_row(
            "Network Throughput",
            "Detect unusual spikes in inbound or outbound traffic that could indicate a breach or a DDoS attempt.",
            "Network I/O",
            "Real-time bandwidth monitoring and packet loss detection.",
            card_on_left=True
        ),
        # 5. Right Card: Early Warning (Product Vision)
        feature_row(
            "AI Early Warning",
            "Pulse doesn't just show graphs. It learns your system's baseline and alerts you to anomalies instantly.",
            "Anomaly Detection",
            "Machine learning powered alerts for behavioral deviations.",
            card_on_left=False
        ),
        width="100%",
        align_items="center",
        padding_top="60px",
    )

# main entry point
# =========================

# MAIN ENTRY POINT (Updated)
# ===============================================================================

def index():
    return rx.vstack(
        navbar(),
                
        rx.center(
            rx.vstack(
                landing_hero(),
                
                # Downward visual indication area
                rx.text("whole detailed explanation comes", color=MUTED, size="4", weight="bold"),
                rx.text("down in clear beautiful formatting way", color=MUTED, size="4", weight="bold"),
                rx.icon(tag="arrow-down", color=TEXT, size=30, margin_top="15px"),
                
                align_items="center",
                width="100%"
            ),
            flex="1",
            width="100%",
            padding="60px 20px",
        ),

        footer(),

        min_height="100vh",
        background=BG,
    )

# HOME
# ================================================================================

def home():

    return rx.vstack(

        navbar(),

        rx.center(
            rx.heading(
                "Home",
                size="8",
                color=GREEN,
            ),
            flex="1",
        ),

        footer(),

        min_height="100vh",
        background=BG,
    )


# LOGIN PAGE
# ===============================================================================
def login_page():
    return rx.vstack(
        navbar(),
        rx.center(
            auth_card(),
            flex="1",
            width="100%",
            padding="40px 20px",
        ),
        footer(),
        min_height="100vh",
        background=BG,
    )

# ===============================================================================
# APP ROUTING
# ===============================================================================

# app and its paths
app = rx.App(
    style=PULSE_STYLE,  #global colors apply
    head_components=[
        rx.script(src="https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit", async_=True, defer=True)
    ]
)

# Landing page (No CAPTCHA needed here)
app.add_page(index, route="/")
# Login page (CAPTCHA script moved here)
app.add_page(login_page, route="/login", on_load=rx.call_script("setTimeout(renderCaptcha, 200);"))
# Protected pages
app.add_page(home, route="/home", on_load=AuthState.check_auth)
app.add_page(about, route="/about", on_load=AuthState.check_auth)
app.add_page(services, route="/services", on_load=AuthState.check_auth)
app.add_page(contact, route="/contact", on_load=AuthState.check_auth)