from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Agendamento, Empresa, Atendente
from django.contrib.auth import get_user_model
import string
import secrets

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    """Formulário customizado para criação de usuários"""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'seu@email.com'
        }),
        help_text='Endereço de email válido para login e comunicações.'
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Seu nome'
        }),
        help_text='Seu primeiro nome.'
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Seu sobrenome'
        }),
        help_text='Seu sobrenome.'
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'nome_usuario'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Customizar campos de senha
        self.fields['password1'].widget = forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite sua senha'
        })
        self.fields['password2'].widget = forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirme sua senha'
        })
        
        # Customizar help texts
        self.fields['username'].help_text = 'Obrigatório. 150 caracteres ou menos. Apenas letras, números e @/./+/-/_ permitidos.'
        self.fields['password1'].help_text = '''
        <ul class="small text-muted">
            <li>Sua senha não pode ser muito similar às suas outras informações pessoais.</li>
            <li>Sua senha deve conter pelo menos 8 caracteres.</li>
            <li>Sua senha não pode ser uma senha comumente usada.</li>
            <li>Sua senha não pode ser inteiramente numérica.</li>
        </ul>
        '''

    def clean_email(self):
        """Validação personalizada do email"""
        email = self.cleaned_data.get('email')
        
        if User.objects.filter(email=email).exists():
            raise ValidationError('Um usuário com este email já existe.')
        
        return email

    def clean_username(self):
        """Validação personalizada do username"""
        username = self.cleaned_data.get('username')
        
        if User.objects.filter(username=username).exists():
            raise ValidationError('Um usuário com este nome já existe.')
        
        # Verificar se não contém espaços
        if ' ' in username:
            raise ValidationError('O nome de usuário não pode conter espaços.')
        
        return username

    def save(self, commit=True):
        """Salvar usuário com campos customizados"""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
        
        return user

class AgendamentoForm(forms.ModelForm):
    """Formulário para agendamentos"""
    
    class Meta:
        model = Agendamento
        fields = ['cliente', 'empresa', 'servico', 'atendente', 'dataHoraInicio', 'dataHoraFim']
        widgets = {
            'dataHoraInicio': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'}
            ),
            'dataHoraFim': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'}
            ),
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'empresa': forms.Select(attrs={'class': 'form-control'}),
            'servico': forms.Select(attrs={'class': 'form-control'}),
            'atendente': forms.Select(attrs={'class': 'form-control'}),
        }

class EmpresaForm(forms.ModelForm):
    """Formulário para empresa"""
    
    class Meta:
        model = Empresa
        fields = ['nome', 'endereco', 'telefone', 'email', 'cnpj']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'endereco': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'cnpj': forms.TextInput(attrs={'class': 'form-control'}),
        }

class AtendenteForm(forms.ModelForm):
    """Formulário customizado para atendentes"""
    
    criar_usuario = forms.BooleanField(
        required=False,
        initial=True,
        label='Criar usuário para login',
        help_text='Marque para criar automaticamente um usuário que poderá fazer login no sistema'
    )
    
    gerar_senha = forms.BooleanField(
        required=False,
        initial=True,
        label='Gerar senha automaticamente',
        help_text='Se marcado, uma senha será gerada automaticamente. Caso contrário, você pode definir uma senha.'
    )
    
    senha_customizada = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Senha personalizada',
        help_text='Deixe em branco para gerar automaticamente'
    )

    class Meta:
        model = Atendente
        fields = ['empresa', 'nome', 'email', 'telefone', 'especialidades']
        widgets = {
            'empresa': forms.Select(attrs={'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'especialidades': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        if self.tenant:
            self.fields['empresa'].queryset = Empresa.objects.filter(tenant=self.tenant)
            # Importar aqui para evitar importação circular
            from .models import Servico
            self.fields['especialidades'].queryset = Servico.objects.filter(tenant=self.tenant)

    def clean_email(self):
        """Validar email único"""
        email = self.cleaned_data.get('email')
        
        # Verificar se já existe um usuário com este email
        if User.objects.filter(email=email).exists():
            if not self.instance.pk or self.instance.user.email != email:
                raise ValidationError('Já existe um usuário com este email.')
        
        return email

    def save(self, commit=True):
        """Salvar atendente e criar usuário se necessário"""
        atendente = super().save(commit=False)
        
        if commit:
            atendente.save()
            self.save_m2m()  # Salvar many-to-many relationships
            
            # Criar usuário se solicitado
            if self.cleaned_data.get('criar_usuario', False):
                user, created = User.objects.get_or_create(
                    email=atendente.email,
                    defaults={
                        'username': atendente.email,
                        'first_name': atendente.nome.split()[0] if atendente.nome else '',
                        'last_name': ' '.join(atendente.nome.split()[1:]) if len(atendente.nome.split()) > 1 else '',
                        'is_active': True,
                    }
                )
                
                if created:
                    # Definir senha
                    if self.cleaned_data.get('gerar_senha', True):
                        import secrets
                        import string
                        senha = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
                        user.set_password(senha)
                        user.save()
                        
                        # Armazenar senha gerada para exibir ao usuário
                        self.senha_gerada = senha
                    elif self.cleaned_data.get('senha_customizada'):
                        user.set_password(self.cleaned_data['senha_customizada'])
                        user.save()
                
                # Associar usuário ao atendente
                atendente.user = user
                atendente.save()
                
                # Adicionar ao grupo Atendentes
                from django.contrib.auth.models import Group
                grupo_atendentes, created = Group.objects.get_or_create(name='Atendentes')
                user.groups.add(grupo_atendentes)
        
        return atendente
