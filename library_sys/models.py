# -- coding: utf-8 --

from datetime import date

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.contrib.auth.models import User, UserManager


class Book(models.Model):
    name = models.CharField("Nome", max_length=100)
    author = models.CharField("Autor(a)", max_length=200)
    year = models.PositiveSmallIntegerField(
        "Ano", validators=[MinValueValidator(1564), MaxValueValidator(date.today().year)]
    )
    publisher = models.CharField("Editora", max_length=100)

    def __str__(self):
        return u'{} - {}'.format(self.author,
                                self.name)

    class Meta:
        verbose_name = u"Livro"
        verbose_name_plural = u"Livros"


class BookItem(models.Model):
    book = models.ForeignKey(Book, verbose_name="Livro")

    def __str__(self):
        return u'№{} {}'.format(self.pk, self.book.name)

    class Meta:
        verbose_name = u"Exemplar"
        verbose_name_plural = u"Exemplares"


# noinspection PyAbstractClass
class Reader(User):
    phone_number = models.CharField(blank=True, verbose_name="Telefone", max_length=16)
    address = models.CharField(verbose_name="Endereço", blank=True, max_length=50)
    objects = UserManager()

    def __str__(self):
        return u'№{} {} {}: {}'.format(
            self.pk, self.first_name,
            self.last_name,
            self.username
        )

    class Meta:
        verbose_name = u"Usuári@"
        verbose_name_plural = u"Usuári@s"


class HistoryItem(models.Model):
    date_taken = models.DateField(verbose_name="Emprestado em")
    date_due = models.DateField(verbose_name="À ser entregue em")
    date_returned = models.DateField(verbose_name="Entregue em", blank=True, null=True)
    fine = models.SmallIntegerField(verbose_name="Multa total", default=0)
    daily_fine = models.SmallIntegerField("Multa diária", default=0)
    is_fine_paid = models.NullBooleanField(verbose_name="Multa paga?", default=False)
    book_item = models.ForeignKey(BookItem)
    reader = models.ForeignKey(Reader)
    
    def __str__(self):
        return u'{}: №{} {} - {}'.format(
            self.reader.username, self.book_item.pk,
            self.book_item.book.author,
            self.book_item.book.name
        )

    class Meta:
        verbose_name = u"Empréstimo"
        verbose_name_plural = u"Empréstimos"
    
    def calculate_fine(self):
        if self.date_due < datetime.date.today():
            if not self.date_returned:
                return self.daily_fine * (datetime.date.today() - self.date_due).days
            elif self.date_returned > self.date_due:
                return self.daily_fine * (self.date_returned - self.date_due).days
            else:
                return 0
        else:
            return 0

    def save(self, *args, **kwargs):
        self.fine = self.calculate_fine()
        super(HistoryItem, self).save(*args, **kwargs)
    