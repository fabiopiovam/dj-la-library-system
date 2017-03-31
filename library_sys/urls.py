from django.conf.urls import url

from . import views
from . import forms

urlpatterns = [
    url(r'^index/$', views.index, name='index'),
    url(r'^$', views.index, name='index'),
    url(r'^search/$', views.search, name='search'),
    url(r'^login/$', forms.LoginFormView.as_view(), name='login'),
    url(r'^logout/$', forms.LogoutView.as_view(), name='logout'),
    url(r'^change_pass/$', views.change_password, name='change_password'),
    url(r'^book_list/$', views.BookListView.as_view(), name='book_list'),
    url(r'^(?P<slug>.*?)/$', views.book, name='book'),
]
