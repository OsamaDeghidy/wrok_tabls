from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # User Management URLs
    path('users/', views.UserListView, name='list'),
    path('users/create/', views.UserCreateView, name='create'),
    path('users/<int:pk>/', views.UserDetailView, name='detail'),
    path('users/<int:pk>/edit/', views.UserEditView, name='edit'),
    path('users/<int:pk>/delete/', views.UserDeleteView, name='delete'),
    
    # Profile URLs
    path('profile/', views.UserProfileView, name='profile'),
    path('profile/edit/', views.UserEditProfileView, name='edit_profile'),
    path('profile/change-password/', views.UserChangePasswordView, name='change_password'),
    
    # Authentication URLs
    path('login/', views.LoginView, name='login'),
    path('logout/', views.LogoutView, name='logout'),
    path('register/', views.RegisterView, name='register'),
    path('forgot-password/', views.ForgotPasswordView, name='forgot_password'),
    path('reset-password/', views.ResetPasswordView, name='reset_password'),
]