from django.contrib import admin
from .models import Usuario, Responsavel, Professor, Gestor, Disciplina, Aluno, PacoteHora, Aula
from django.contrib.auth.models import User
from django import forms
import datetime

# Register your models here.

# Widget de horário com apenas 00 e 30 minutos

class CustomTimeSelect(forms.Select):
    def __init__(self, *args, **kwargs):
        times = [
            (datetime.time(hour, minute).strftime('%H:%M'), f'{hour:02d}:{minute:02d}')
            for hour in range(0, 24)
            for minute in (0, 30)
        ]
        super().__init__(choices=times, *args, **kwargs)

# Formulário customizado para o modelo Aula
class AulaAdminForm(forms.ModelForm):
    hora_inicio = forms.TimeField(widget=CustomTimeSelect(attrs={'class': 'vTimeField'}))
    hora_fim = forms.TimeField(widget=CustomTimeSelect(attrs={'class': 'vTimeField'}))

    class Meta:
        model = Aula
        fields = '__all__'



class AulaAdmin(admin.ModelAdmin):
    form = AulaAdminForm

admin.site.register(Aula, AulaAdmin)
admin.site.register(Professor)
admin.site.register(Responsavel)
admin.site.register(Disciplina)
admin.site.register(PacoteHora)
admin.site.register(Usuario)
admin.site.register(Gestor)
admin.site.register(Aluno)


class PacoteHoraAdmin(admin.ModelAdmin):
    list_display = (
        "responsavel",
        "aluno",
        "horas_contratadas",
        "valor_hora",
        "data_contrato",
    )
    list_filter = ("responsavel", "aluno")
    autocomplete_fields = ("responsavel", "aluno")
    
    search_fields = (
        "responsavel__user__first_name",
        "responsavel__user__last_name",
        "responsavel__user__username",
        "aluno__nome",
    )