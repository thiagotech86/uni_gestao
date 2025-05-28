from django import forms
from .models import Aula, Aluno, Professor, Usuario, Disciplina
from django.contrib.auth.forms import AuthenticationForm
import datetime

class CustomTimeSelect(forms.Select):
    def __init__(self, *args, **kwargs):
        # Agora usamos o objeto datetime.time como chave
        times = [
            (datetime.time(hour, minute), f'{hour:02d}:{minute:02d}')
            for hour in range(6, 23)  # De 06:00 até 22:30
            for minute in (0, 30)
        ]
        super().__init__(choices=times, *args, **kwargs)


class CustomLoginForm(AuthenticationForm):
    cpf = forms.CharField(label='cpf', max_length=100)
    password = forms.CharField(label='Senha', widget=forms.PasswordInput)


class SignUpForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['cpf', 'nome', 'email', 'telefone', 'senha']


class AddAulaForm(forms.ModelForm):
    local = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={"placeholder": "Local da aula", "class": "form-control"}
        ),
        label=""
    )

    disciplina = forms.ModelChoiceField(
        queryset=Disciplina.objects.all(),
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Disciplina"
    )

    data_inicio = forms.DateField(
    required=True,
    widget=forms.DateInput(
        format='%Y-%m-%d',  # <-- ESSENCIAL para que o campo mostre a data corretamente
        attrs={
            "placeholder": "Data de início",
            "class": "form-control",
            "type": "date"
        }
    ),
    label="Data da Aula"
)

    hora_inicio = forms.TimeField(
        required=True,
        initial=datetime.time(6, 0),
        widget=CustomTimeSelect(attrs={"class": "form-control"}),
        label="Hora de início"
    )

    hora_fim = forms.TimeField(
        required=True,
        initial=datetime.time(22, 0),
        widget=CustomTimeSelect(attrs={"class": "form-control"}),
        label="Hora de fim"
    )

    aluno = forms.ModelChoiceField(
        queryset=Aluno.objects.all(),
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Aluno"
    )

    professor = forms.ModelChoiceField(
        queryset=Professor.objects.all(),
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Professor"
    )

    descricao = forms.CharField(
        required=True,
        widget=forms.Textarea(
            attrs={"placeholder": "Descrição", "class": "form-control"}
        ),
        label="Descrição da aula"
    )

    class Meta:
        model = Aula
        fields = [
            'local', 'disciplina', 'aluno', 'professor',
            'data_inicio', 'hora_inicio', 'hora_fim', 'descricao'
        ]

def clean(self):
    cleaned_data = super().clean()
    aluno = cleaned_data.get('aluno')
    professor = cleaned_data.get('professor')
    data_inicio = cleaned_data.get('data_inicio')
    hora_inicio = cleaned_data.get('hora_inicio')
    hora_fim = cleaned_data.get('hora_fim')

    if aluno and professor and data_inicio and hora_inicio and hora_fim:
        if Aula.objects.filter(
            aluno=aluno,
            professor=professor,
            data_inicio=data_inicio,
            hora_inicio=hora_inicio,
            hora_fim=hora_fim
        ).exists():
            raise forms.ValidationError(
                "Já existe uma aula cadastrada com os mesmos dados: aluno, professor, data, hora de início e hora de fim."
            )

    return cleaned_data
