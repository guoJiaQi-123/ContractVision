from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

router = DefaultRouter()
router.register('v1/users/manage', views.UserManagementViewSet, basename='user-manage')

urlpatterns = [
    path('v1/auth/register/', views.UserRegisterView.as_view(), name='user-register'),
    path('v1/auth/login/', views.UserLoginView.as_view(), name='user-login'),
    path('v1/auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('v1/auth/change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('v1/auth/password-reset/', views.PasswordResetView.as_view(), name='password-reset'),
    path('v1/users/profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('', include(router.urls)),
]
