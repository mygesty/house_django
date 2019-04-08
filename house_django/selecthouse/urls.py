from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.selecthouse),
    url(r'^(\d+)/', views.choose_page),
]
