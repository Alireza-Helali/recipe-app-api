from django.urls import path

from .views import CreateApiView, CreateTokenView, ManageUserView

app_name = 'user'

urlpatterns = [
    path('create/', CreateApiView.as_view(), name='create'),
    path('token/', CreateTokenView.as_view(), name='token'),
    path('me/', ManageUserView.as_view(), name='me'),
]
