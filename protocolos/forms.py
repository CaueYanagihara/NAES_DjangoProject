from django import forms
from .models import Agendamento, Empresa
from django.utils import timezone

class AgendamentoForm(forms.ModelForm):
    data_inicio = forms.DateField(label="Data de Início", widget=forms.DateInput(attrs={'type': 'date'}))
    hora_inicio = forms.TimeField(label="Hora de Início", widget=forms.TimeInput(attrs={'type': 'time'}))
    data_fim = forms.DateField(label="Data de Fim", widget=forms.DateInput(attrs={'type': 'date'}))
    hora_fim = forms.TimeField(label="Hora de Fim", widget=forms.TimeInput(attrs={'type': 'time'}))

    class Meta:
        model = Agendamento
        fields = ["data_inicio", "hora_inicio", "data_fim", "hora_fim", "status", "cliente", "empresa", "servico", "atendente"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            if self.instance.dataHoraInicio:
                self.fields['data_inicio'].initial = self.instance.dataHoraInicio.date().strftime('%Y-%m-%d')
                self.fields['hora_inicio'].initial = self.instance.dataHoraInicio.time().strftime('%H:%M')
            if self.instance.dataHoraFim:
                self.fields['data_fim'].initial = self.instance.dataHoraFim.date().strftime('%Y-%m-%d')
                self.fields['hora_fim'].initial = self.instance.dataHoraFim.time().strftime('%H:%M')

    def clean(self):
        cleaned_data = super().clean()
        data_inicio = cleaned_data.get("data_inicio")
        hora_inicio = cleaned_data.get("hora_inicio")
        data_fim = cleaned_data.get("data_fim")
        hora_fim = cleaned_data.get("hora_fim")
        if data_inicio and hora_inicio:
            cleaned_data["dataHoraInicio"] = timezone.make_aware(
                timezone.datetime.combine(data_inicio, hora_inicio)
            )
        if data_fim and hora_fim:
            cleaned_data["dataHoraFim"] = timezone.make_aware(
                timezone.datetime.combine(data_fim, hora_fim)
            )
        return cleaned_data

    def save(self, commit=True):
        self.instance.dataHoraInicio = self.cleaned_data["dataHoraInicio"]
        self.instance.dataHoraFim = self.cleaned_data["dataHoraFim"]
        return super().save(commit=commit)


class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ["cnpj", "nomeFantasia", "descricao", "rua", "numero", "bairro", "cidade", "estado", "cep", "telefone", "email", "ativo"]
        widgets = {
            'cnpj': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'XX.XXX.XXX/XXXX-XX'}),
            'nomeFantasia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da empresa'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descrição da empresa'}),
            'rua': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da rua'}),
            'numero': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número'}),
            'bairro': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bairro'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cidade'}),
            'estado': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'UF', 'maxlength': '2'}),
            'cep': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'XXXXX-XXX'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(XX) XXXXX-XXXX'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@empresa.com'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'cnpj': 'CNPJ',
            'nomeFantasia': 'Nome Fantasia',
            'descricao': 'Descrição',
            'rua': 'Rua',
            'numero': 'Número',
            'bairro': 'Bairro',
            'cidade': 'Cidade',
            'estado': 'Estado (UF)',
            'cep': 'CEP',
            'telefone': 'Telefone',
            'email': 'E-mail',
            'ativo': 'Empresa Ativa',
        }
