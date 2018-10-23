from django.apps import apps
from django.contrib import admin

# Register your models here.
from usercontroller.models import User


class UserAdmin(admin.ModelAdmin):
    readonly_fields = ('created',)


admin.site.register(User, UserAdmin)

myapp = apps.get_app_config('usercontroller')
# myapp.models

for model in myapp.models.values():
    try:
        admin.site.register(model)
    except Exception as e:
        pass