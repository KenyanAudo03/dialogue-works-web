from django.urls import path
from . import views

app_name = 'authentication'  # Add this line to namespace your URLs

urlpatterns = [
    path('register_step_one/', views.register_step_one, name='register_step_one'),
    path('verify_email/<str:token>/', views.verify_email, name='verify_email'),
    path('register_step_two/', views.register_step_two, name='register_step_two'),
    path('register_step_three/', views.register_step_three, name='register_step_three'),
]
