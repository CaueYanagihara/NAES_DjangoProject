from django import forms
from .models import Agendamento
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
                self.fields['data_inicio'].initial = self.instance.dataHoraInicio.date()
                self.fields['hora_inicio'].initial = self.instance.dataHoraInicio.time()
            if self.instance.dataHoraFim:
                self.fields['data_fim'].initial = self.instance.dataHoraFim.date()
                self.fields['hora_fim'].initial = self.instance.dataHoraFim.time()

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
