import reflex as rx
from supabase import create_client
from dotenv import load_dotenv
import os
import time
import smtplib
from email.message import EmailMessage
import os

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

#contact class here
class ContactState(rx.State):
    contact_name: str = ""
    contact_message: str = ""
    feedback_message: str = ""
    feedback_type: str = "" 

    # 1. EXPLICIT SETTERS: These force the UI to sync with the backend
    def set_contact_name(self, name_input: str):
        self.contact_name = name_input

    def set_contact_message(self, message_input: str):
        self.contact_message = message_input

    @rx.event
    def handle_submit(self, user_email: str):
        self.feedback_message = "Sending..."
        self.feedback_type = "success"
        yield  # Updates UI immediately

        try:
            # Grab your secure credentials
            sender_email = os.getenv("GMAIL_ADDRESS")
            app_password = os.getenv("GMAIL_APP_PASSWORD")

            if not sender_email or not app_password:
                self.feedback_message = "Server email configuration is missing."
                self.feedback_type = "error"
                return

            # Construct the email package using the synced state variables
            msg = EmailMessage()
            msg.set_content(f"Name: {self.contact_name}\nRegistered Email: {user_email}\n\nMessage:\n{self.contact_message}")
            msg['Subject'] = f"New Pulse Inquiry from {self.contact_name}"
            msg['From'] = sender_email
            msg['To'] = sender_email  

            # Connect to Google and send it
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(sender_email, app_password)
                smtp.send_message(msg)

            # Success cleanup
            self.feedback_message = "Message sent successfully!"
            self.feedback_type = "success"
            
            # Wipe the text area clean after a successful send
            self.contact_message = ""  
            self.contact_name = ""

        except Exception as e:
            self.feedback_message = f"Failed to send: {str(e)}"
            self.feedback_type = "error"

#Session Dealing logic comes here
class AuthState(rx.State):
    email: str = ""
    password: str = ""

    # NEW: Separated message states!
    login_message: str = ""
    login_message_type: str = ""
    
    signup_message: str = ""
    signup_message_type: str = ""
    
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
    def login(self):
        self.login_message = ""
        self.login_message_type = ""
            
        if not self.email or not self.password:
            self.login_message = "Please enter your email and password."
            self.login_message_type = "error"
            return

        try:
            response = supabase.auth.sign_in_with_password({
                "email": self.email,
                "password": self.password,
            })

            self.is_authenticated = True
            self.login_message = "Login successful!"
            self.login_message_type = "success"

            return rx.redirect("/home")

        except Exception:
            self.is_authenticated = False
            self.login_message = "Incorrect email or password."
            self.login_message_type = "error"

    @rx.event
    def signup(self):
        self.signup_message = ""
        self.signup_message_type = ""
        #cooldown Timer (60 seconds)
        current_time = time.time()
        if current_time - self.last_signup_attempt < 60:
            remaining = int(60 - (current_time - self.last_signup_attempt))
            self.signup_message = f"Please wait {remaining} seconds before requesting another email."
            self.signup_message_type = "error"
            return

        if not self.email or not self.password:
            self.signup_message = "Please enter your email and password."
            self.signup_message_type = "error"
            return

        if len(self.password) < 6:
            self.signup_message = "Password must be at least 6 characters."
            self.signup_message_type = "error"
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
                self.signup_message = "This email is already registered. Please log in."
                self.signup_message_type = "error"
            elif response.user and response.session is None:
                self.signup_message = "Registration successful! Check your email to verify your account."
                self.signup_message_type = "success"
            else:
                self.signup_message = "Account created successfully!"
                self.signup_message_type = "success"

        except Exception as e:
            error_msg = str(e).lower()
            if "rate limit" in error_msg or "too many requests" in error_msg:
                self.signup_message = "Too many requests. Please wait a moment before trying again."
            else:
                self.signup_message = str(e)
            self.signup_message_type = "error"

    @rx.event
    def logout(self):
        # Clear backend state instantly
        self.is_authenticated = False
        self.login_message = ""
        self.login_message_type = ""
        self.signup_message = ""
        self.signup_message_type = "e"
        self.email = ""
        self.password = ""
        self.turnstile_token = ""
    #Fire client-side script to wipe token and redirect immediately
        return [
            rx.call_script("window.turnstileToken = null;"),
            rx.redirect("/")
            ]

    #==================================================================================
    #msgs state resetting
    @rx.event  # <-- CRITICAL: Added missing event decorator
    def reset_auth_state(self):
        """Wipes all inputs and messages clean when visiting the login page."""
        self.email = ""
        self.password = ""
        self.login_message = ""
        self.login_message_type = ""
        self.signup_message = ""
        self.signup_message_type = ""
        self.turnstile_token = ""
    
# NAVBAR
# ===============================================================================
def navbar():
    return rx.vstack(
        rx.hstack(
            rx.heading("Pulse", size="7", color=GREEN),
            rx.spacer(),
            
            rx.cond(
                AuthState.is_authenticated,
                # WHAT LOGGED IN USERS SEE: Links + Logout Button
                rx.hstack(
                    rx.link("Home", href="/home", color=TEXT),
                    rx.link("Services", href="/services", color=TEXT),
                    rx.link("Contact", href="/contact", color=TEXT),
                    rx.button(
                        "Logout",
                        background=GREEN,
                        color=BG,
                        border_radius="20px",
                        padding_x="24px",
                        on_click=AuthState.logout,
                        cursor="pointer",
                        _hover={"background": "#a2ce55"}, # Slight shade shift on hover
                    ),
                    spacing="6",
                    align="center",
                ),
                # WHAT PUBLIC USERS SEE: Just Login/Signup Button
                rx.button(
                    "Login/Signup",
                    background=TEXT,
                    color=BG,
                    border_radius="20px",
                    padding_x="24px",
                    cursor="pointer",
                    transition="all 0.2s ease",
                    _hover={
                        "background": GREEN,        # Shifts from white/text color to your neon green!
                        "color": BG,
                        "transform": "translateY(-2px)", # Tiny lift effect
                    },
                    on_click=rx.redirect("/login"),
                ),
            ),
            width="100%",
            align="center",
        ),
        
        # Green bottom line
        rx.box(
            width="100%",
            height="3px",
            background=GREEN,
            margin_top="15px",
        ),
        
        width="100%",
        background=NAV_BG,
        padding="20px 40px 0 40px",
    )

#================================================================================
# AUTHENTICATION COMPONENTS (Split into 3 columns for scrollable.png blueprint)
# ===============================================================================
def signup_card():
    return rx.vstack(
        rx.heading("SignUp", size="8", color=TEXT, margin_bottom="20px", width="100%", text_align='center'),
        
        rx.input(placeholder="name (optional)", width="100%", background="#252D29", border_color=BORDER, color=TEXT, id="signup_name", name="signup_name"),
        rx.input(placeholder="email (mandatory)", type="email", on_change=AuthState.set_email, width="100%", background="#252D29", border_color=BORDER, color=TEXT, id="signup_email", name="signup_email", auto_complete=False),
        rx.input(placeholder="password (mandatory)", type="password", on_change=AuthState.set_password, width="100%", background="#252D29", border_color=BORDER, color=TEXT, id="signup_password", name="signup_password", auto_complete=False),
        
        rx.button(
            "signup",
            on_click=AuthState.signup,
            width="100%",
            background=BG,                 
            color=TEXT,
            border=f"1px solid {BORDER}",  
            margin_top="10px",
            padding="20px",
            cursor="pointer",
            transition="all 0.2s ease",
            _hover={
                "background": GREEN,       
                "color": BG,
                "border_color": GREEN,
            },
        ),
        
        rx.cond(
            AuthState.signup_message != "",
            rx.text(
                AuthState.signup_message, 
                color=rx.cond(AuthState.signup_message_type == "success", GREEN, YELLOW), 
                text_align="center"
            ),
        ),
        
        width="350px",
        padding="40px",
        background=CARD_BG,
        border="1px solid",
        border_color=BORDER,
        border_radius="20px",
        box_shadow="0 20px 60px rgba(0, 0, 0, 0.35)",
    )

def auth_middle_section():
    return rx.vstack(
        
        rx.script(src="https://challenges.cloudflare.com/turnstile/v0/api.js?onload=onloadTurnstileCallback", async_=True, defer=True),
        rx.script(
            f"""
            function onloadTurnstileCallback() {{
                if (window.turnstile) {{
                    window.turnstile.render('#my-captcha-box', {{
                        sitekey: '{TURNSTILE_SITE_KEY}',
                        theme: 'dark',
                        callback: function(token) {{
                            // Automatically populate token
                            window.turnstileToken = token;
                        }},
                    }});
                }}
            }}
            """
        ),
        rx.html('<div id="my-captcha-box"></div>'),
        
        rx.link("forgot pass?", color=MUTED, margin_top="15px", _hover={"color": GREEN}),
        
        align_items="center",
        justify_content="center",
        width="280px",
        spacing="6",
    )

def login_card():
    return rx.vstack(
        rx.heading("Login", size="8", color=TEXT, margin_bottom="20px", width="100%", text_align="center"),
        
        rx.input(placeholder="gmail", type="email", on_change=AuthState.set_email, width="100%", background="#252D29", border_color=BORDER, color=TEXT, id="login_email", name="login_email", auto_complete=False),
        rx.input(placeholder="password", type="password", on_change=AuthState.set_password, width="100%", background="#252D29", border_color=BORDER, color=TEXT, id="login_password", name="login_password", auto_complete=False),
        
        rx.button(
            "Login",
            width="100%",
            background=BG,                 
            color=TEXT,
            border=f"1px solid {BORDER}",  
            margin_top="10px",
            padding="20px",
            cursor="pointer",
            transition="all 0.2s ease",
            _hover={
                "background": GREEN,       
                "color": BG,
                "border_color": GREEN,
            },
            on_click=AuthState.login,
        ),

        rx.cond(
            AuthState.login_message != "",
            rx.text(
                AuthState.login_message, 
                color=rx.cond(AuthState.login_message_type == "success", GREEN, YELLOW), 
                text_align="center"
            ),
        ),
        
        width="350px",
        padding="40px",
        background=CARD_BG,
        border="1px solid",
        border_color=BORDER,
        border_radius="20px",
        box_shadow="0 20px 60px rgba(0, 0, 0, 0.35)",
    )

# ===============================================================================
# LOGIN PAGE ASSEMBLY
# ===============================================================================
def log_page():
    return rx.vstack(
        navbar(),
        
        rx.center(
            # The FLEX container lines up our 3 separate sections horizontally!
            rx.flex(
                signup_card(),
                auth_middle_section(),
                login_card(),
                direction="row",  # This makes them sit side-by-side
                spacing="8",
                align_items="center",
                justify_content="center",
                width="100%",
                max_width="1200px"
            ),
            flex="1",
            width="100%",
            padding="40px 20px",
        ),
        
        footer(),
        min_height="100vh",
        background=BG,
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
                "© Pulse",
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
#service card for service page
def service_card(title: str, description: str, icon_tag: str):
    """A reusable blueprint for the 6 service offerings."""
    return rx.vstack(
        # We use Reflex's built-in Lucide icons (matches the aesthetic perfectly)
        rx.icon(tag=icon_tag, size=40, color=YELLOW, margin_bottom="10px"),
        
        rx.heading(title, size="5", color=TEXT, text_align="center"),
        rx.text(description, color=MUTED, size="3", text_align="center", line_height="1.5"),
        
        padding="30px",
        background=CARD_BG,
        border=f"1px solid {BORDER}",
        border_radius="20px",
        align_items="center",
        justify_content="center",
        width="100%",
        min_height="0px",
        transition="all 0.3s ease",
        _hover={
            "border_color": GREEN,
            "box_shadow": f"0 10px 30px rgba(183, 227, 107, 0.15)",
            "transform": "translateY(-5px)" # Tiny hover lift
        }
    )
# PROTECTED PAGES (Restored)
# ================================================================================
def home():
    return rx.vstack(
        navbar(),
        rx.center(rx.heading("Home Dashboard", size="8", color=GREEN), flex="1"),
        footer(),
        min_height="100vh", background=BG,
    )

def services():
    return rx.vstack(
        navbar(),
        
        rx.center(
            rx.vstack(
                # --- HERO SECTION ---
                rx.heading("I BUILD SOLUTIONS THAT GROW YOUR BUSINESS", size="8", color=TEXT, text_align="center", margin_bottom="10px"),
                rx.text("SMART. SCALABLE. IMPACTFUL.", color=GREEN, size="5", weight="bold", margin_bottom="50px"),
                
                # --- 3-COLUMN GRID ---
                rx.grid(
                    service_card(
                        "Business Dashboards", 
                        "See everything clearly. Track what matters. Make better decisions.", 
                        "bar-chart-3"
                    ),
                    service_card(
                        "Smart Automation", 
                        "Automate repetitive work. Save time. Reduce errors. Increase productivity.", 
                        "cpu"
                    ),
                    service_card(
                        "Customer Systems", 
                        "Understand your customers better and deliver exceptional experiences.", 
                        "users"
                    ),
                    service_card(
                        "Intelligent AI", 
                        "Smart systems that learn, predict and help you stay one step ahead.", 
                        "brain-circuit"
                    ),
                    service_card(
                        "Scalable Products", 
                        "Modern, secure and scalable products built to grow with your business.", 
                        "rocket"
                    ),
                    service_card(
                        "AI Agent Solutions", 
                        "Smart AI agents that talk, assist and get things done for your business.", 
                        "bot"
                    ),
                    columns="3",     # Creates 3 equal columns
                    spacing="6",     # Gap between cards
                    width="100%",
                    max_width="1100px"
                ),
                
                # --- BOTTOM CTA ---
                rx.box(
                    rx.heading("I DON'T JUST BUILD APPS. I BUILD GROWTH ENGINES.", size="6", color=YELLOW, text_align="center"),
                    margin_top="60px",
                    padding="30px",
                    border=f"1px solid {YELLOW}",
                    border_radius="20px",
                    background="rgba(242, 209, 107, 0.05)",
                    box_shadow=f"0 0 20px rgba(242, 209, 107, 0.1)"
                ),
                
                align_items="center",
                width="100%",
                padding_y="60px", # Gives breathing room from navbar and footer
            ),
            flex="1",
            width="100%",
        ),
        
        footer(),
        min_height="100vh", 
        background=BG,
    )

def contact_page():
    return rx.vstack(
        navbar(),  
        
        # The Layout Wrapper: Takes up all available width to center its content
        rx.center(
            
            # The Actual Contact Card
            rx.vstack(
                rx.heading("Get in Touch", size="8", color=TEXT, margin_bottom="10px"),
                rx.text("Have questions about Pulse? Send us a message.", color=MUTED, margin_bottom="30px", text_align="center"),
                
                # Form Inputs
                rx.input(
                    placeholder="Your Name", 
                    on_change=ContactState.set_contact_name,
                    width="100%", 
                    height="45px",
                    background="rgba(37, 45, 41, 0.85)", 
                    color=TEXT, 
                    padding="15px",
                    border_color=YELLOW,
                    box_shadow=f"0 0 8px {YELLOW}",
                    transition="all 0.3s ease",
                    _hover={"border_color": GREEN, "box_shadow": f"0 0 12px {GREEN}"},
                    _focus={"border_color": GREEN, "box_shadow": f"0 0 12px {GREEN}"}
                ),

                rx.input(
                    value=AuthState.email,
                    disabled=True, 
                    width="100%", 
                    height="45px",
                    background="rgba(37, 45, 41, 0.5)", # Slightly darker to indicate it's locked
                    color=MUTED, 
                    padding="15px",
                    border_color=BORDER,
                ),
                rx.text_area(
                    placeholder="How can we help?",
                    value=ContactState.contact_message,
                    on_change=ContactState.set_contact_message, 
                    width="100%", 
                    background="rgba(37, 45, 41, 0.85)", 
                    color=TEXT, 
                    padding="15px", 
                    min_height="120px",
                    border_color=YELLOW,
                    box_shadow=f"0 0 8px {YELLOW}",
                    transition="all 0.3s ease",
                    _hover={"border_color": GREEN, "box_shadow": f"0 0 12px {GREEN}"},
                    _focus={"border_color": GREEN, "box_shadow": f"0 0 12px {GREEN}"}
                ),
                
                rx.button(
                    "Send Message",
                    # Pass the AuthState email into our new function
                    on_click=lambda: ContactState.handle_submit(AuthState.email),
                    width="100%",
                    background=BG,                 
                    color=TEXT,
                    border=f"1px solid {BORDER}",  
                    margin_top="10px",
                    padding="20px",
                    cursor="pointer",
                    transition="all 0.3s ease",
                    _hover={
                        "background": GREEN,       
                        "color": BG,
                        "border_color": GREEN,
                        "box_shadow": f"0 0 15px {GREEN}"
                    },
                ),
                
                # --- CARD SIZING & BACKGROUND (Moved here!) ---
                width="100%",
                max_width="480px",
                height="75vh",
                max_height="700px",
                padding="40px",
                justify_content="center", 
                align_items="center",
                
                background_image="url('/contact_card.png')",
                background_size="cover",
                background_position="center",
                
                border=f"1px solid {BORDER}",
                border_radius="20px",
                box_shadow="0 20px 60px rgba(0, 0, 0, 0.6)",
                overflow="hidden",
            ),
            
            # --- WRAPPER PROPERTIES ---
            width="100%",
            flex="1", 
        ),
        
        footer(),  
        
        # --- PAGE PROPERTIES ---
        min_height="100vh",
        width="100%",
        background=BG,
    )

# LANDING PAGE COMPONENTS
# ===============================================================================
def landing_hero():
    return rx.vstack(
        # Huge PULSE heading
        rx.image(
            src="/hero_card.png",  # Points to assets/hero_card.png
            width="100%",
            height="auto",
            border_radius="30px",  # Curves the image edges to match the box
        ),
        
        # Blueprint Box Styling
        width="80%",
        max_width="1000px",
        margin_top="-25px",       
        margin_bottom="0px", 
        box_shadow="0 20px 60px rgba(0, 0, 0, 0.35)",
        border=f"1px solid {BORDER}",
        border_radius="30px",
        background=CARD_BG,
    )
    
# LANDING PAGE COMPONENTS
# ===============================================================================
def feature_card(image_path: str):
    """Creates a stylized card displaying a full-bleed image with a hover animation."""
    return rx.box(
        rx.image(
            src=image_path,
            width="100%",
            height="auto",
            # The image naturally fills the box now
        ),
        background=CARD_BG,

        border_radius="20px",
        border=f"1px solid {BORDER}",
        width="45%",  
        transition="all 0.3s ease",
        overflow="hidden", #CRITICAL: Forces the image to respect the rounded corners
        _hover={
            "transform": "translateY(-10px)",
            "border_color": GREEN,
            "box_shadow": "0 10px 30px rgba(183, 227, 107, 0.15)",
        }
    )

def feature_row(text_title: str, text_desc: str, image_path: str, card_on_left: bool = False):
    """Creates a zigzag row with text on one side and an image card on the other."""
    text_section = rx.vstack(
        rx.heading(text_title, size="7", color=TEXT, margin_bottom="10px"),
        rx.text(text_desc, color=MUTED, size="4", line_height="1.6"),
        align_items="start",
        width="45%", 
    )
    
    # We now pass the image_path instead of title/description
    card_section = feature_card(image_path)
    
    items = [card_section, text_section] if card_on_left else [text_section, card_section]
    
    return rx.flex(
        *items,
        direction="row",
        justify_content="space-between",
        align_items="center",
        width="100%",
        max_width="1000px",
        margin_bottom="50px", 
    )
    
#=====================================================================================
# landing features 
def landing_features():
    """Assembles all the features in the requested zigzag pattern with actual images."""
    return rx.vstack(
        # 1. Right Card: RAM
        feature_row(
            "Memory Optimization", 
            "Track memory allocation in real-time. Pulse monitors active processes to prevent out-of-memory crashes before they happen.",
            "/ram.png",  # <-- Points to assets/ram.png
            card_on_left=False
        ),
        # 2. Left Card: CPU
        feature_row(
            "Processing Power",
            "Analyze thread loads and processor bottlenecks. Identify rogue processes consuming too many cycles.",
            "/cpu.png",
            card_on_left=True
        ),
        # 3. Right Card: GPU
        feature_row(
            "Hardware Acceleration",
            "Keep an eye on compute-heavy workloads. Perfect for AI and machine learning infrastructure monitoring.",
            "/gpu.png",
            card_on_left=False
        ),
        # 4. Left Card: Network
        feature_row(
            "Network Throughput",
            "Detect unusual spikes in inbound or outbound traffic that could indicate a breach or a DDoS attempt.",
            "/networkio.png",
            card_on_left=True
        ),
        # 5. Right Card: Early Warning 
        feature_row(
            "AI Early Warning",
            "Pulse doesn't just show graphs. It learns your system's baseline and alerts you to anomalies instantly.",
            "/anomaly.png",
            card_on_left=False
        ),
        width="100%",
        align_items="center",
        padding_top="10px", 
    )

# MAIN ENTRY POINT (Updated)
# ===============================================================================
def index():
    return rx.vstack(
        navbar(),
                
        rx.center(
            rx.vstack(
                landing_hero(),
                
                # Visual transition arrow with reduced spacing, and placeholder text removed
                rx.icon(tag="arrow-down", color=TEXT, size=35, margin_bottom="20px"),
                
                landing_features(),
                
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

# ===============================================================================
# APP ROUTING

# app and its paths
app = rx.App(
    style=PULSE_STYLE,  #global colors apply
    head_components=[
        rx.script(src="https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit", async_=True, defer=True)
    ]
)

#Public Pages
app.add_page(index, route="/", title="Pulse")

#Login Page (Properly triggers the reset function on load)
app.add_page(log_page, route="/login", title="Login | Pulse", on_load=AuthState.reset_auth_state)

#Protected Pages (Requires Authentication)
app.add_page(home, route="/home", title="Dashboard | Pulse", on_load=AuthState.check_auth)
app.add_page(services, route="/services", title="Services | Pulse", on_load=AuthState.check_auth)

#Contact Page (Made public so unauthenticated users can email you)
app.add_page(contact_page, route="/contact", title="Contact | Pulse", on_load=AuthState.check_auth)
