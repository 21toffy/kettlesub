from django.urls import path
from .user import *
from .auth import *

urlpatterns = [
    path('register/', RegistrationView.as_view(), name='user-registration'),
    path('verify-otp/', VerificationView.as_view(), name='otp-verification'),
    path('login/', LoginView.as_view(), name='login'),
    path('refresh-token/', RefreshTokenView.as_view(), name='refresh-token'),
    path('logout/', Logout.as_view(), name='logout'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/<str:uidb64>/<str:token>/', ResetPasswordView.as_view(), name='reset-password'),

]
