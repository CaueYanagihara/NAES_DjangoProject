from django.urls import path
# Importar suas views
from .views import index, sobre, contato, escolher_cadastro, DashboardView, dashboard_data

urlpatterns = [
    path("", index, name="index"),
    path("sobre/", sobre, name="sobre"),
    path("contato/", contato, name="contato"),
    path("escolher-cadastro/", escolher_cadastro, name="escolher-cadastro"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path('api/dashboard-data/', dashboard_data, name='dashboard-data'),
]