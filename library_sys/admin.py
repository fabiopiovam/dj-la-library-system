from datetime import date

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.utils import formats
from django.urls import reverse
from django.db.models import F, Q, Min
from django import forms

from tags.forms import FormTags, set_tags

from .models import (Author, Publisher, Book, BookItem,
                     Reader, HistoryItem, Category)


class CategoryAdmin(admin.ModelAdmin):
    exclude = ['slug']

    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index.
        """
        return {}


class AuthorAdmin(admin.ModelAdmin):
    pass


class PublisherAdmin(admin.ModelAdmin):
    pass


class BookItemAdminListFilterAvailable(admin.SimpleListFilter):
    title = 'disponibilidade'
    parameter_name = 'item_available_check'

    def lookups(self, request, model_admin):
        options = model_admin.model.AVAILABLE_CHOICES

        return options

    def queryset(self, request, queryset):
        if self.value():
            value = int(self.value())
            if value == queryset.model.AVAILABLE:
                return queryset.filter(
                    Q(book__available=True) &
                    Q(available=True) &
                    Q(book__book_item_total__gt=F('book__book_item_unavailable')),
                    Q(last_history_item_id__isnull=True) |
                    Q(last_history_item_id__isnull=False) &
                    Q(last_date_returned__isnull=False)
                )
            elif value == queryset.model.UNAVAILABLE:
                return queryset.filter(
                    Q(book__available=False) |
                    Q(available=False) |
                    Q(book__book_item_total=F('book__book_item_unavailable')) |
                    Q(last_history_item_id__isnull=False) &
                    Q(last_date_returned__isnull=True)
                )
            elif value == queryset.model.BORROWED:
                return queryset.filter(
                    last_history_item_id__isnull=False,
                    last_date_returned__isnull=True
                )
            elif value == queryset.model.PENDING:
                return queryset.filter(
                    last_history_item_id__isnull=False,
                    last_date_returned__isnull=True,
                    last_date_due__lt=date.today()
                )
            else:
                return queryset
        else:
            return queryset


class BookItemAdmin(admin.ModelAdmin):
    fields = ('book', 'available', 'comments')
    list_display = ('__str__', 'available_check', 'comments', 'last_loan')
    search_fields = ('book__id', 'book__title', 'book__publisher__name',
                     'book__author__name', 'historyitem__reader__username')
    list_filter = [BookItemAdminListFilterAvailable]

    def last_loan(self, obj):
        obj_available = self.model.obj_availables.filter(id=obj.id)
        link_borrow = '''<a href="%s?book_item_id=%s" target="_blank">
            [Emprestar]</a>''' % (reverse('admin:library_sys_historyitem_add'),
                                  obj.id)
        if not obj.last_history_item_id:
            return link_borrow if obj_available else '-'

        reader = Reader.objects.get(id=obj.last_reader_id)

        if not obj.last_date_returned:
            link_borrow = ''
            status = 'à ser entregue em %s' % formats.date_format(
                                                  obj.last_date_due,
                                                  "SHORT_DATE_FORMAT")
        else:
            link_borrow = '%s<hr>' % link_borrow if obj_available else ''
            status = 'devolvido em %s' % formats.date_format(
                                             obj.last_date_returned,
                                             "SHORT_DATE_FORMAT")

        link = reverse('admin:library_sys_historyitem_change',
                       args=[obj.last_history_item_id])

        return '''%s<a href="%s" target="_blank" title="visualizar detalhes">
                  %s<br> para %s<br>%s</a>
               ''' % (link_borrow, link,
                      formats.date_format(obj.last_date_taken,
                                          "DATE_FORMAT"),
                      reader, status)
    last_loan.allow_tags = True
    last_loan.short_description = 'Último empréstimo'

    def available_check(self, obj):
        return True if BookItem.obj_availables.filter(id=obj.id) else False

    available_check.boolean = True
    available_check.allow_tags = True
    available_check.short_description = 'disponível'

    '''
    Disabled actions to prevent erros in update of models.Book.book_item_total
    when BookItem is deleted.
    The posible solution to call delete method of model when user want remove
    items selected found here but i prefer unable the actions:
    http://stackoverflow.com/questions/1471909/django-model-delete-not-triggered
    '''
    actions = None


class BookAdminListFilterAvailable(admin.SimpleListFilter):
    title = 'disponível'
    parameter_name = 'available_check'

    def lookups(self, request, model_admin):
        options = [(True, _('Sim')), (False, _('Não'))]

        return options

    def queryset(self, request, queryset):
        if self.value():
            if self.value() == 'True':
                return queryset.filter(available__exact=True,
                    book_item_total__gt=F('book_item_unavailable'))
            else:
                return queryset.filter(
                    Q(available__exact=False) |
                    Q(book_item_total__exact=F('book_item_unavailable')) &
                    Q(book_item_unavailable__gt=0))
        else:
            return queryset


class BookForm(FormTags):
    class Meta:
        model = Book
        fields = '__all__'


class BookAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,
         {'fields': ['title', 'author', 'publisher', 'year', 'book_item_total',
                     'activated', 'available']}),
        ("Informações complementares",
         {'fields': ['published_date', 'isbn', 'category', 'tags', 'synopsis',
                     'review', 'cover', 'file']}),
    ]

    list_display = ('title', 'author', 'publisher', 'year',
                    'activated', 'book_item_link',
                    'available_items')
    search_fields = ('title', 'author__name', 'publisher__name')
    filter_horizontal = ('category',)
    list_filter = ['activated', BookAdminListFilterAvailable]

    form = BookForm

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        set_tags(obj, form.cleaned_data['tags'])

    def available_items(self, obj):
        available_items = obj.book_item_total - obj.book_item_unavailable
        if not available_items:
            label = 'Nenhum'
        elif available_items == 1:
            label = '%s item' % available_items
        else:
            label = '%s itens' % available_items

        change_url = reverse('admin:library_sys_historyitem_changelist')
        link = '''<a href="%s?book_item__book=%s&q=%s"
            title="visualizar os exemplares emprestados"
            target="_blank">
            %s</a>''' % (change_url, obj.id, obj.title, label)
        return link

    available_items.allow_tags = True
    available_items.short_description = 'disponível'

    def book_item_link(self, obj):
        change_url = reverse('admin:library_sys_bookitem_changelist')

        if not obj.book_item_total:
            label = 'Nenhum'
        elif obj.book_item_total == 1:
            label = '%s item' % obj.book_item_total
        else:
            label = '%s itens' % obj.book_item_total

        link = '''<a href="%s?book_id=%s&q=%s" target="_blank">
                    %s</a>''' % (change_url, obj.id,
                                    obj.title, label)
        return link

    book_item_link.allow_tags = True
    book_item_link.short_description = 'exemplares'


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


class HistoryBookItemAvailableForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.id:
            choices = [(self.instance.book_item.id, self.instance.book_item)]
        elif 'book_item_id' in kwargs['initial']:
            book_item = BookItem.obj_availables.filter(
                            id=kwargs['initial']['book_item_id'])
            #import pdb;pdb.set_trace()
            choices = [(None, '')] if not book_item else [(book_item[0].id,
                                                           book_item[0])]
        else:
            choices = [(None, '')]

        book_item_available = BookItem.obj_availables.values(
                 'book_id',
                 'book__title',
                 'book__author__name',
                 'book__publisher__name'
        ).annotate(id_min=Min('id'))

        for x in book_item_available:
            label = '%s (%s - %s)' % (
                        x['book__title'],
                        x['book__author__name'],
                        x['book__publisher__name']
                    )
            choices.append((x['id_min'], label))

        self.fields['book_item'].choices = choices

    class Meta:
        model = BookItem
        exclude = ['available']


class HistoryItemAdminListFilterStatus(admin.SimpleListFilter):
    title = 'status'
    parameter_name = 'status_check'

    def lookups(self, request, model_admin):
        options = model_admin.model.STATUS_CHOICES

        return options

    def queryset(self, request, queryset):
        if self.value():
            value = int(self.value())
            if value == queryset.model.RETURNED:
                return queryset.filter(date_returned__isnull=False)
            elif value == queryset.model.BORROWED:
                return queryset.filter(date_returned__isnull=True)
            elif value == queryset.model.PENDING:
                return queryset.filter(date_returned__isnull=True,
                                       date_due__lt=date.today())
            else:
                return queryset
        else:
            return queryset


class HistoryAdmin(admin.ModelAdmin):

    form = HistoryBookItemAvailableForm

    date_hierarchy = 'date_due'
    fields = ('reader', 'book_item', 'date_taken', 'date_due', 'date_returned')
    list_display = ('book_item', 'reader', 'date_taken', 'date_due',
                    'date_returned')
    list_filter = (HistoryItemAdminListFilterStatus,
                   'reader__username',
                   'reader', 'book_item__book')
    search_fields = (
        'reader__first_name',
        'reader__last_name',
        'reader__username',
        'book_item__book__title',
        'book_item__book__author__name',
    )

    actions = None

admin.site.register(Category, CategoryAdmin)
admin.site.register(Author, AuthorAdmin)
admin.site.register(Publisher, PublisherAdmin)
admin.site.register(Book, BookAdmin)
admin.site.register(BookItem, BookItemAdmin)
admin.site.unregister(User)
admin.site.register(Reader, ReaderAdmin)
admin.site.register(HistoryItem, HistoryAdmin)
