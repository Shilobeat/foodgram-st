from django.urls import include, path

urlpatterns = [
    path('', include('api.users.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include('api.recipes.urls')),
]