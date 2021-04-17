from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(RegUser)
admin.site.register(Tag)
admin.site.register(Game)
admin.site.register(PurchasedGame)
admin.site.register(GameReview)
admin.site.register(GameSale)
