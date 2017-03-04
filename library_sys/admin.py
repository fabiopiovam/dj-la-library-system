from django.contrib import admin

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from .models import Book, BookItem, Reader, HistoryItem


class BookAdmin(admin.ModelAdmin):
    search_fields = ('name', 'author')


class ReaderChangeForm(UserChangeForm):
    password = ReadOnlyPasswordHashField(
        label=_("Password"),
        help_text=_("Raw passwords are not stored, so there is no way to see "
                    "this user's password, but you can change the password "
                    "using <a href=\"password/\">this form</a>."))

    def clean_password(self):
        return self.initial["password"]


class Meta:
    model = Reader


class ReaderAdmin(UserAdmin):
    form = ReaderChangeForm
    list_display = ('username', 'first_name',
                    'is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name',
                                         'email', 'phone_number', 'address')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff',
                                       'is_superuser', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Groups'), {'fields': ('groups',)}),
    )
    search_fields = ('username', 'first_name', 'last_name')


class HistoryAdmin(admin.ModelAdmin):
    list_display = ('reader', 'book_item', 'fine', 'is_fine_paid')
    list_filter = ('reader', 'book_item__book')
    search_fields = (
        'reader__first_name',
        'reader__last_name',
        'reader__username',
        'book_item__book__name',
        'book_item__book__author',
    )

admin.site.register(Book, BookAdmin)
admin.site.register(BookItem)
admin.site.unregister(User)
admin.site.register(Reader, ReaderAdmin)
admin.site.register(HistoryItem, HistoryAdmin)
