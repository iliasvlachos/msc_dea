from django.contrib import admin
from .models import Tier, UserTier

# Register your models here.
admin.site.register(Tier)
admin.site.register(UserTier)
