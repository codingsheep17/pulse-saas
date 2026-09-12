import reflex as rx
from reflex.plugins.sitemap import SitemapPlugin

plugin = SitemapPlugin()

config = rx.Config(
    app_name="pulse",
    disable_plugins=[plugin],
)