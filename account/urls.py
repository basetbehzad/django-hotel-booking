from django.urls import path
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.generic import TemplateView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from account.views import RegisterUserView, UserProfileView, SessionLoginView, ProfilePageView, OwnerIncomeView, \
    LogoutView, current_user


@require_GET
def csrf_token_view(request):
    return JsonResponse({'status': 'success'})


app_name = 'account'
urlpatterns = [
    path('api/user/register/', RegisterUserView.as_view(), name='register'),
    path('api/user/', current_user, name="current_user"),
    path('api/user/token/', TokenObtainPairView.as_view(), name='user_token_obtain'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='user_token_refresh'),
    path('api/csrf-token/', csrf_token_view),
    path('api/user/profile/', UserProfileView.as_view(), name='user_profile'),
    path('login/', TemplateView.as_view(template_name='login_form.html')),
    path('api/session-login/', SessionLoginView.as_view(), name='session-login'),
    path('api/logout/', LogoutView.as_view(), name='user_logout'),
    path('profile/', ProfilePageView.as_view(), name='profile-page'),
    path('api/user/income/', OwnerIncomeView.as_view(), name='owner-income'),

]
