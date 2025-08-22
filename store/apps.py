from django.apps import AppConfig

class StoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'store'

    # The 'ready' method and the 'import store.signals'
    # line that were here before can now be safely deleted.