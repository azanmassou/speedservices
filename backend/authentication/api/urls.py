from django.urls import path
from .views import RegisterView, LoginView, CustomTokenRefreshView, LogoutView
from .healthcheckview import HealthCheckView


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'), # POST
    path('login/', LoginView.as_view(), name='login'),          # POST
    path('refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'), # POST
    path('logout/', LogoutView.as_view(), name='logout'),       # POST
    path('health/', HealthCheckView.as_view(), name='health_check'), # GET /api/auth/health/
]