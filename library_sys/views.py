# -*- coding: utf-8 -*-

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import render_to_response, render, redirect
from django.db.models.query import EmptyQuerySet
from django.views.generic import ListView

from .models import Book, HistoryItem

def index(request):
    return render_to_response('index.html', {'user': request.user})

def home(request):
    return render_to_response('index.html', {'username': request.user.first_name})


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
                          {'form': PasswordChangeForm(request.user), 'message': messages})
        else:
            messages.error(request, "Senha incorreta")
            return render(request, "change_pass.html",
                          {'form': PasswordChangeForm(request.user), 'message': messages})
    return render(request, "change_pass.html",
                  {'form': PasswordChangeForm(request.user), 'message': messages})


def search(request):
    error = False
    if 'name' in request.GET or 'author' in request.GET:
        name = request.GET['name']
        author = request.GET['author']
        if not name and not author:
            error = True
        elif name and author:
            books = Book.objects.filter(author__icontains=author, name__icontains=name)
            return render_to_response('search_results.html',
                                      {'books': books, 'query': author + '-' + name})
        elif name:
            books = Book.objects.filter(name__icontains=name)
            return render_to_response('search_results.html', {'books': books, 'query': name})
        elif author:
            books = Book.objects.filter(author__icontains=author)
            return render_to_response('search_results.html', {'books': books, 'query': author})
    return render_to_response('search_form.html', {'error': error})


class BookListView(ListView):
    model = HistoryItem
    template_name = 'book_list.html'
    context_object_name = 'books'

    def get_queryset(self):
        if self.request.user.is_authenticated():
            return super(BookListView, self).get_queryset().filter(reader=self.request.user)
        else:
            return EmptyQuerySet

    def get_context_data(self, **kwargs):
        context = super(BookListView, self).get_context_data(**kwargs)
        total_fine = 0
        if self.get_queryset() != EmptyQuerySet:
            for item in self.get_queryset():
                if item.fine > 0 and not item.is_fine_paid:
                    total_fine = total_fine + item.fine
            context['total_fine'] = total_fine
        return context
    