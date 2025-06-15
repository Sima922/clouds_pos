from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, ClientSubscription

class UserInline(admin.TabularInline):
    model = User
    fields = ('email', 'first_name', 'last_name', 'role')
    extra = 0
    readonly_fields = ('email',)
    can_delete = False
    verbose_name_plural = 'Members'

@admin.register(ClientSubscription)
class ClientSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'owner', 'tier', 'active', 'member_count', 'created_at', 'expires_at')
    inlines = [UserInline]

    def member_count(self, obj):
        return obj.members.exclude(pk=obj.owner_id).count()
    member_count.short_description = 'Extra Users'

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('email','password')}),
        ('Personal', {'fields': ('first_name','last_name','phone','role')}),
        ('Subscription', {'fields': ('subscription',)}),
        ('Permissions', {'fields': ('is_active','is_staff','is_superuser','groups','user_permissions')}),
        ('Dates', {'fields': ('last_login','date_joined')}),
    )
    add_fieldsets = (
        (None,{
            'classes':('wide',),
            'fields':('email','first_name','last_name','phone','role','subscription','password1','password2'),
        }),
    )
    list_display  = ('email','first_name','last_name','role','subscription')
    list_filter   = ('role','subscription')
    search_fields = ('email','first_name','last_name')
    ordering      = ('email',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(subscription=request.user.subscription)
