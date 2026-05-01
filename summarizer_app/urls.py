from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('summarize/', views.summarize, name='summarize'),
    # path('download/', views.download_summary, name='download'),
]