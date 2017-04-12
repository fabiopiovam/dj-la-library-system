# -- coding: utf-8 --

from datetime import datetime, date
import glob
import os

from django.db import models
from django.db.models import F, Q
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.contrib.auth.models import User, UserManager
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.urls import reverse

from .validators import FileValidator


class Author(models.Model):

    name = models.CharField("autor(a)", max_length=200)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "autor(a)"


class Publisher(models.Model):

    name = models.CharField("editora", max_length=200)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "editora"


class Category(models.Model):

    title = models.CharField('categoria', max_length=160)
    description = models.TextField('descrição', null=True, blank=True)
    slug = models.SlugField(max_length=200)

    class Meta:
        verbose_name = u"categoria"

    def __str__(self):
        return u'%s' % self.title

    def save(self, *args, **kwargs):
        if not self.id:
            self.slug = slugify(self.title)

        super().save()


class BookActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(activated=True)


class Book(models.Model):

    def get_absolute_url(self):
        return reverse('book',
                       args=[str(self.slug)])

    def get_upload_to_image(self, filename):
        ext = filename[-3:].lower()
        if ext == 'peg':
            ext = 'jpeg'

        return 'book/cover/%s_%s.%s' % (self.slug,
                   datetime.now().strftime('%Y%m%d%H%M%S'),
                   ext)

    def get_upload_to_file(self, filename):
        ext = filename[-3:].lower()

        return 'book/file/%s_%s.%s' % (self.slug,
                                       datetime.now().strftime('%Y%m%d%H%M%S'),
                                       ext)

    author = models.ForeignKey(Author, verbose_name="autor(a)")
    publisher = models.ForeignKey(Publisher, verbose_name="editora")
    category = models.ManyToManyField(Category, verbose_name=u"categorias",
                                      blank=True)
    title = models.CharField("título", max_length=100)
    slug = models.SlugField(max_length=200)
    year = models.PositiveSmallIntegerField(
        "Ano", blank=True, null=True, 
        validators=[MinValueValidator(1564),
                    MaxValueValidator(date.today().year)]
    )
    activated = models.BooleanField('ativo', default=True,
                                    help_text=_('''Caso desmarque esta opção
                                        o registro não aparecerá no site.'''))
    available = models.BooleanField('disponível', default=True,
                                    help_text=_('''Caso desmarque esta opção
                                        o registro aparecerá no site, porém,
                                        como 'indisponível'.'''))
    book_item_total = models.PositiveSmallIntegerField(
        'total de exemplares',
        validators=[MinValueValidator(1)],
        default=0)
    book_item_unavailable = models.PositiveSmallIntegerField(
        'total de exemplares indisponíveis',
        default=0)
    published_date = models.DateField(verbose_name="data da publicação",
                                      blank=True, null=True)
    synopsis = models.TextField(verbose_name='sinopse',
                              null=True, blank=True)
    review = models.TextField(verbose_name='resenha',
                              null=True, blank=True)
    isbn = models.CharField(verbose_name='ISBN',
                            max_length=30, 
                            null=True, blank=True,
                            help_text=_('''International Standard Book Number
                            <a href='https://pt.wikipedia.org/wiki/International_Standard_Book_Number' 
                            title='Mais informações'
                            target='_blank'>(?)</a>'''))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    cover_height = models.PositiveSmallIntegerField('altura da capa',
                                                    blank=True, null=True)
    cover_width = models.PositiveSmallIntegerField('largura da capa',
                                                   blank=True, null=True)

    cover = models.ImageField('capa', upload_to=get_upload_to_image,
                              height_field='cover_height',
                              width_field='cover_width',
                              blank=True, null=True,
                              validators=[FileValidator(
                                  max_size=1 * 1024 * 1024)],
                              help_text=_('''Selecione a imagem de capa
                               do livro, normalmente nos formatos
                               jpg, png, gif, etc.'''))

    file = models.FileField('arquivo', upload_to=get_upload_to_file,
                            blank=True, null=True,
                            validators=[FileValidator(
                                  max_size=5 * 1024 * 1024,
                                  allowed_mimetypes=('application/pdf',
                                                     'application/epub+zip'))],
                            help_text=_('''Selecione o arquivo do livro
                             para download, normalmente nos formatos
                             pdf, epub, etc.'''))

    ''' Managers '''
    objects = models.Manager()
    obj_active = BookActiveManager()

    class Meta:
        verbose_name = "livro"
        verbose_name_plural = "livros"

    def __str__(self):
        return u'{} - {}'.format(self.author, self.title)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__original_book_item_total = self.book_item_total

    def clean(self):
        original_book_item_total = self._Book__original_book_item_total
        book_item_total = self.book_item_total

        if (original_book_item_total
            and book_item_total < original_book_item_total):
            raise ValidationError({
                'book_item_total':
                _('Para reduzir o total de exemplares você deve excluir individualmente'),
            })

    def save(self, *args, **kwargs):
        if not self.id:
            self.slug = slugify(self.title)
            super().save()

            i = 0
            to_persist = []
            while i < self.book_item_total:
                to_persist.append(BookItem(book_id=self.id))
                i += 1

            BookItem.objects.bulk_create(to_persist)
        else:
            ''' UPDATE BOOK ITEM TOTAL FIELD '''
            if self.book_item_total > self.__original_book_item_total:
                i = self.__original_book_item_total
                to_persist = []
                while i < self.book_item_total:
                    to_persist.append(BookItem(book_id=self.id))
                    i += 1

                BookItem.objects.bulk_create(to_persist)

            ''' MEDIA MAINTENANCE '''
            obj_book = Book.objects.get(id=self.id)

            if obj_book.cover and self.cover not in [obj_book.cover]:
                for fl in glob.glob("%s/%s*" % (settings.MEDIA_ROOT,
                                                obj_book.cover)):
                    os.remove(fl)

            if obj_book.file and self.cover not in [obj_book.file]:
                for fl in glob.glob("%s/%s*" % (settings.MEDIA_ROOT,
                                                obj_book.file)):
                    os.remove(fl)

            super().save()

    def delete(self):
        obj_photo = Book.objects.get(id=self.id)
        super().delete()

        if obj_photo.cover:
            for fl in glob.glob("%s/%s*" % (settings.MEDIA_ROOT,
                                            obj_photo.cover)):
                os.remove(fl)


class BookItemAvailableManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(
            Q(book__available=True) &
            Q(available=True) &
            Q(book__book_item_total__gt=F('book__book_item_unavailable')),
            Q(last_history_item_id__isnull=True) |
            Q(last_history_item_id__isnull=False) &
            Q(last_date_returned__isnull=False)
        )


class BookItem(models.Model):

    AVAILABLE = 1
    UNAVAILABLE = 2
    BORROWED = 3
    PENDING = 4

    AVAILABLE_CHOICES = (
        (AVAILABLE, 'Disponível'),
        (UNAVAILABLE, 'Indisponível'),
        (BORROWED, 'Emprestado'),
        (PENDING, 'Entrega pendente')
    )

    book = models.ForeignKey(Book, verbose_name="livro")
    available = models.BooleanField('disponível', default=True)
    comments = models.TextField(verbose_name='observações',
                                null=True, blank=True)

    last_history_item_id = models.SmallIntegerField(
                               verbose_name="ultimo empréstimo",
                               blank=True, null=True)
    last_reader_id = models.SmallIntegerField(verbose_name="ultimo leitor(a)",
                                              blank=True, null=True)
    last_date_taken = models.DateField(verbose_name="data ultimo empréstimo",
                                       blank=True, null=True)
    last_date_due = models.DateField(verbose_name="previsão de entrega",
                                       blank=True, null=True)
    last_date_returned = models.DateField(verbose_name="entregue em",
                                     blank=True, null=True)

    ''' Managers '''
    objects = models.Manager()
    obj_availables = BookItemAvailableManager()

    class Meta:
        verbose_name = u"exemplar"
        verbose_name_plural = u"exemplares"
        ordering = ['book__title', 'book__author__name']

    def __str__(self):
        return '№{} {} ({} - {})'.format(self.pk,
                                     self.book.title,
                                     self.book.author.name,
                                     self.book.publisher.name)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__original_book = self.book_id
        self.__original_available = self.available

    def save(self):
        if not self.id:
            super().save()
            book = Book.objects.get(id=self.book.id)
            book.book_item_total += 1
            if not self.available:
                book.book_item_unavailable += 1
            book.save()
        else:
            if self.book.id != self.__original_book:
                book = Book.objects.get(id=self.book.id)
                book.book_item_total += 1
                book.save()

                original_book = Book.objects.get(id=self.__original_book)
                original_book.book_item_total -= 1
                original_book.save()

            if self.__original_available != self.available:
                book = Book.objects.get(id=self.book.id)
                if not self.available:
                    book.book_item_unavailable += 1
                else:
                    book.book_item_unavailable -= 1
                book.save()

            super().save()

    def delete(self):
        super().delete()
        book = Book.objects.get(id=self.book.id)
        if (book.book_item_total > 0):
            book.book_item_total -= 1
            book.save()


# noinspection PyAbstractClass
class Reader(User):

    phone_number = models.CharField(blank=True, verbose_name="Telefone", max_length=16)
    address = models.CharField(verbose_name="Endereço", blank=True, max_length=50)
    objects = UserManager()

    class Meta:
        verbose_name = u"usuári@"

    def __str__(self):
        return '№{} {} {}: {}'.format(
            self.pk, self.first_name,
            self.last_name,
            self.username
        )


class HistoryItem(models.Model):

    RETURNED = 1
    BORROWED = 2
    PENDING = 3

    STATUS_CHOICES = (
        (RETURNED, 'Devolvido'),
        (BORROWED, 'Emprestado'),
        (PENDING, 'Entrega pendente')
    )

    book_item = models.ForeignKey(BookItem, verbose_name="exemplar")
    reader = models.ForeignKey(Reader, verbose_name="leitor(a)")
    date_taken = models.DateField(verbose_name="emprestado em")
    date_due = models.DateField(verbose_name="à ser entregue em")
    date_returned = models.DateField(verbose_name="entregue em",
                                     blank=True, null=True)
    fine = models.SmallIntegerField(verbose_name="multa total", default=0)
    daily_fine = models.SmallIntegerField("multa diária", default=0)
    is_fine_paid = models.NullBooleanField(verbose_name="multa paga?",
                                           default=False)

    class Meta:
        verbose_name = u"empréstimo"
        verbose_name_plural = u"empréstimos"
        ordering = ['-date_taken']

    def __str__(self):
        return u'{}: №{} {} - {}'.format(
            self.reader.username, self.book_item.pk,
            self.book_item.book.author,
            self.book_item.book.title
        )

    def calculate_fine(self):
        if self.date_due < date.today():
            if not self.date_returned:
                return self.daily_fine * (date.today() - self.date_due).days
            elif self.date_returned > self.date_due:
                return self.daily_fine * (self.date_returned - self.date_due).days
            else:
                return 0
        else:
            return 0

    def set_latest_history_item(self, book_item_id):
        try:
            last_book_item = HistoryItem.objects.filter(
            book_item=book_item_id).latest('date_taken')
        except ObjectDoesNotExist:
            last_book_item = None

        book_item = BookItem.objects.get(id=book_item_id)
        if last_book_item:
            book_item.last_history_item_id = last_book_item.id
            book_item.last_reader_id = last_book_item.reader.id
            book_item.last_date_taken = last_book_item.date_taken
            book_item.last_date_due = last_book_item.date_due
            book_item.last_date_returned = last_book_item.date_returned
        else:
            book_item.last_history_item_id = None
            book_item.last_reader_id = None
            book_item.last_date_taken = None
            book_item.last_date_due = None
            book_item.last_date_returned = None
        book_item.save()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.id:
            self.__original_book_item = self.book_item
        self.__original_date_returned = self.date_returned

    def save(self, *args, **kwargs):
        self.fine = self.calculate_fine()

        if not self.id:
            super().save()

            ''' PERSIST VALUES OF LAST BORROWED BOOK ITEM '''
            book_item = BookItem.objects.get(id=self.book_item.id)
            book_item.last_history_item_id = self.id
            book_item.last_reader_id = self.reader.id
            book_item.last_date_taken = self.date_taken
            book_item.last_date_due = self.date_due
            book_item.last_date_returned = self.date_returned
            book_item.save()

            ''' COUNT BOOK ITEM UNAVAILABLE '''
            if not self.date_returned:
                book = Book.objects.get(id=self.book_item.book_id)
                book.book_item_unavailable += 1
                book.save()
        else:
            ''' COUNT BOOK ITEM UNAVAILABLE '''
            if self.__original_book_item.id != self.book_item.id:
                if self.__original_date_returned == self.date_returned:
                    if not self.date_returned:
                        book = Book.objects.get(
                                   id=self.__original_book_item.book_id)
                        book.book_item_unavailable -= 1
                        book.save()

                        book = Book.objects.get(id=self.book_item.book_id)
                        book.book_item_unavailable += 1
                        book.save()
                else:
                    if not self.__original_date_returned:
                        book = Book.objects.get(
                                   id=self.__original_book_item.book_id)
                        book.book_item_unavailable -= 1
                        book.save()
                    if not self.date_returned:
                        book = Book.objects.get(id=self.book_item.book_id)
                        book.book_item_unavailable += 1
                        book.save()
            else:
                if self.__original_date_returned != self.date_returned:
                    if not self.__original_date_returned:
                        book = Book.objects.get(id=self.book_item.book_id)
                        book.book_item_unavailable -= 1
                        book.save()
                    if not self.date_returned:
                        book = Book.objects.get(id=self.book_item.book_id)
                        book.book_item_unavailable += 1
                        book.save()

            super().save()

            ''' PERSIST VALUES OF LAST BORROWED BOOK ITEM '''
            if self.__original_book_item.last_history_item_id == self.id:
                if self.__original_book_item.id != self.book_item.id:
                    self.set_latest_history_item(self.__original_book_item.id)

                book_item = BookItem.objects.get(id=self.book_item.id)
                book_item.last_history_item_id = self.id
                book_item.last_reader_id = self.reader.id
                book_item.last_date_taken = self.date_taken
                book_item.last_date_due = self.date_due
                book_item.last_date_returned = self.date_returned
                book_item.save()

    def delete(self):
        id = self.id
        super().delete()

        ''' COUNT BOOK ITEM UNAVAILABLE '''
        if not self.date_returned:
            book = Book.objects.get(id=self.book_item.book_id)
            book.book_item_unavailable -= 1
            book.save()

        ''' PERSIST VALUES OF LAST BORROWED BOOK ITEM '''
        if self.book_item.last_history_item_id == id:
            self.set_latest_history_item(self.book_item.id)
