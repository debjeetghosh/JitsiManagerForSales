from django.urls import path
from accounts.views import *

app_name = 'accounts'
urlpatterns = [
    # path('register/', RegisterView.as_view(), name='register'),
    path('login/', login_view, name='login'),
    path('verify-otp/', VerifyOtpView.as_view(), name='verify-otp'),
    path('logout/', logout_view, name='logout'),
    path('login/submit/', login_submit, name='login_submit'),
    path('create/sales-person/', CreateUserView.as_view(), name="create_creator"),
    path('create/admin/', CreateAdminView.as_view(), name="create_admin"),
    path('create/location/', LocationCreateView.as_view(), name="create_location"),
    path('location/<int:pk>/update/', LocationUpdateView.as_view(), name="update_location"),
    path('location/<int:pk>/delete/', LocationDeleteView.as_view(), name="delete_location"),
    path('locations/', LocationListView.as_view(), name="location_list"),
    path('locations/api/', LocationApiView.as_view(), name="location_api"),
    path('admins/', AdminListView.as_view(), name="admin_list"),
    path('sales-person/<int:pk>/delete/', DeleteUserView.as_view(), name="delete_creator"),
    path('user/<int:pk>/update/', UpdateUserPassword.as_view(), name="update_user_password"),
    path('admins/<int:pk>/update/', AdminUpdateView.as_view(), name="admin_update"),
    path('', dashboard, name='dashboard'),
]
