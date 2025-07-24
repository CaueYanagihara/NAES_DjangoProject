from django import forms
from .models import Agendamento, Empresa, Tenant, Atendente
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
import string
import secrets

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

class AtendenteForm(forms.ModelForm):
    """Formulário para cadastro de atendente que também cria usuário do sistema"""
    
    senha = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite uma senha para o atendente'
        }),
        help_text='Senha que o atendente usará para acessar o sistema',
        validators=[validate_password]
    )
    
    confirmar_senha = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirme a senha'
        }),
        help_text='Digite a mesma senha anterior para confirmação'
    )
    
    gerar_senha_automatica = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text='Marque para gerar uma senha automática e segura'
    )

    class Meta:
        model = Atendente
        fields = ['empresa', 'nome', 'email', 'telefone', 'especialidades']
        widgets = {
            'empresa': forms.Select(attrs={'class': 'form-control'}),
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome completo do atendente'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@exemplo.com'
            }),
            'telefone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(11) 99999-9999'
            }),
            'especialidades': forms.CheckboxSelectMultiple(),
        }
        help_texts = {
            'email': 'Este email será usado para login no sistema',
            'especialidades': 'Selecione os serviços que este atendente pode realizar'
        }

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        if self.tenant:
            # Filtrar empresas e especialidades por tenant
            self.fields['empresa'].queryset = Empresa.objects.filter(tenant=self.tenant)
            from .models import Servico
            self.fields['especialidades'].queryset = Servico.objects.filter(tenant=self.tenant)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        senha = cleaned_data.get('senha')
        confirmar_senha = cleaned_data.get('confirmar_senha')
        gerar_senha_automatica = cleaned_data.get('gerar_senha_automatica')
        
        # Verificar se email já existe como usuário
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError(f'Já existe um usuário cadastrado com o email {email}')
        
        # Verificar senhas apenas se não for gerar automática
        if not gerar_senha_automatica:
            if senha and confirmar_senha:
                if senha != confirmar_senha:
                    raise forms.ValidationError('As senhas não coincidem')
            elif not senha:
                raise forms.ValidationError('Senha é obrigatória ou marque "Gerar senha automática"')
        
        return cleaned_data

    def save(self, commit=True):
        atendente = super().save(commit=False)
        
        if self.tenant:
            atendente.tenant = self.tenant
        
        if commit:
            # Verificar se deve gerar senha automática
            if self.cleaned_data.get('gerar_senha_automatica'):
                # Gerar senha segura automaticamente
                senha_automatica = self.gerar_senha_segura()
                self.senha_gerada = senha_automatica
            else:
                senha_automatica = self.cleaned_data['senha']
                self.senha_gerada = None
            
            # Criar usuário do sistema para o atendente
            user = User.objects.create_user(
                username=atendente.email,  # Username será o email
                email=atendente.email,
                password=senha_automatica,
                first_name=atendente.nome.split()[0] if atendente.nome else '',
                last_name=' '.join(atendente.nome.split()[1:]) if len(atendente.nome.split()) > 1 else ''
            )
            
            atendente.user = user
            atendente.save()
            
            # Salvar especialidades (many-to-many)
            if hasattr(self, 'cleaned_data') and 'especialidades' in self.cleaned_data:
                atendente.especialidades.set(self.cleaned_data['especialidades'])
        
        return atendente
    
    def gerar_senha_segura(self, tamanho=12):
        """Gera uma senha segura automaticamente"""
        caracteres = string.ascii_letters + string.digits + "!@#$%&*"
        senha = ''.join(secrets.choice(caracteres) for _ in range(tamanho))
        return senha

# Atualizar formulário de cadastro de usuário para usar email como username
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'seu@email.com'
        }),
        help_text='Digite um e-mail válido que será seu login'
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Seu primeiro nome'
        }),
        help_text='Digite seu primeiro nome'
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Seu sobrenome'
        }),
        help_text='Digite seu sobrenome'
    )

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Remover campo username e usar email
        if 'username' in self.fields:
            del self.fields['username']
        
        # Customizar widgets dos campos padrão
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Digite uma senha segura'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirme sua senha'
        })
        
        # Customizar help texts
        self.fields['password1'].help_text = '''
        <ul class="small text-muted">
            <li>Sua senha não pode ser muito similar às suas outras informações pessoais.</li>
            <li>Sua senha deve conter pelo menos 8 caracteres.</li>
            <li>Sua senha não pode ser uma senha comum.</li>
            <li>Sua senha não pode ser inteiramente numérica.</li>
        </ul>
        '''
        self.fields['password2'].help_text = 'Digite a mesma senha anterior, para verificação.'

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Este email já está cadastrado no sistema.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.username = self.cleaned_data["email"]  # Username será o email
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
        return user
