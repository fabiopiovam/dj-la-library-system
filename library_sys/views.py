# -*- coding: utf-8 -*-

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import render_to_response, render, redirect
from django.db.models.query import EmptyQuerySet
from django.views.generic import ListView
from django.core.exceptions import ObjectDoesNotExist

from .models import Book, HistoryItem


def index(request):
    return render_to_response('index.html', {'user': request.user})


def home(request):
    return render_to_response('index.html',
                              {'username': request.user.first_name})


def change_password(request):
    user = request.user
    if not user.is_authenticated():
        return redirect('/login/')
    if request.method == 'POST':
        form = PasswordChangeForm(user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            messages.success(request, "Senha alterada")
            return render(request, "change_pass.html",
                          {'form': PasswordChangeForm(request.user),
                           'message': messages})
        else:
            messages.error(request, "Senha incorreta")
            return render(request, "change_pass.html",
                          {'form': PasswordChangeForm(request.user),
                           'message': messages})
    return render(request, "change_pass.html",
                  {'form': PasswordChangeForm(request.user),
                   'message': messages})


def search(request):
    error = False
    if 'title' in request.GET or 'author' in request.GET:
        title = request.GET['title']
        author = request.GET['author']
        if not title and not author:
            error = True
        elif title and author:
            books = Book.obj_active.filter(author__name__icontains=author,
                                        title__icontains=title)
            return render_to_response('search_results.html',
                                      {'books': books,
                                       'query': author + '-' + title})
        elif title:
            books = Book.obj_active.filter(title__icontains=title)
            return render_to_response('search_results.html',
                                      {'books': books, 'query': title})
        elif author:
            books = Book.obj_active.filter(author__name__icontains=author)
            return render_to_response('search_results.html',
                                      {'books': books, 'query': author})
    return render_to_response('search_form.html', {'error': error})


def book(request, slug):

    try:
        book = Book.obj_active.get(slug=slug)
    except ObjectDoesNotExist:
        book = None

    return render_to_response('details.html',
                              {'book': book})


class BookListView(ListView):
    model = HistoryItem
    template_name = 'book_list.html'
    context_object_name = 'books'

    def get_queryset(self):
        if self.request.user.is_authenticated():
            return super().get_queryset().filter(reader=self.request.user)
        else:
            return EmptyQuerySet

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total_fine = 0
        if self.get_queryset() != EmptyQuerySet:
            for item in self.get_queryset():
                if item.fine > 0 and not item.is_fine_paid:
                    total_fine = total_fine + item.fine
            context['total_fine'] = total_fine
        return context
