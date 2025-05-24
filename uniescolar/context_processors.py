from .models import Professor

def nav_access_permissions(request):
    can_add_aula = False
    if request.user.is_authenticated:
        is_professor = False
        if not request.user.is_anonymous:
            try:
                # Se Professor.nome (PK) é o User, podemos verificar assim:
                is_professor = Professor.objects.filter(pk=request.user.pk).exists()
            except TypeError: # Pode acontecer se request.user.pk for None para AnonymousUser
                pass

        if request.user.is_superuser or is_professor:
            can_add_aula = True
    return {'can_add_aula_permission': can_add_aula}