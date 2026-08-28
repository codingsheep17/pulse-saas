import reflex as rx

plugins = rx.plugins.SitemapPlugin()
config= rx.Config(
    app_name="pulse",
    disable_plugins=[plugins],
)