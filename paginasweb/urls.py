from django.urls import path
# Importar suas views
from .views import PaginaInicial, SobreView, ContatoView
from .views import EscolherCadastroView

urlpatterns = [
    path("", PaginaInicial.as_view(), name="index" ),
    path("sobre/", SobreView.as_view(), name="sobre"),
    path("contato/", ContatoView.as_view(), name="contato"),
    path("escolher-cadastro/", EscolherCadastroView.as_view(), name="escolher-cadastro"),
]