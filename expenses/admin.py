from django.contrib import admin

# Register your models here.
from .models import Brand, Campaign, Schedule, Expense

admin.site.register(Brand)
admin.site.register(Campaign)
admin.site.register(Schedule)
admin.site.register(Expense)
