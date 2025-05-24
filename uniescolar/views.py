from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib import messages
from .forms import SignUpForm, AddAulaForm 
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from .models import Aula, Aluno, Professor, Responsavel, Gestor, Disciplina
from datetime import datetime, timedelta, date 
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django import forms 
import json

# Create your views here.

# Função auxiliar para verificar se o usuário é Gestor
def is_gestor_check(user):
    return user.is_authenticated and hasattr(user, 'gestor_profile')

# Tela Home / Login
def home(request):
    horas_contratadas_aluno_filtrado = None
    horas_utilizadas_aluno_filtrado = None
    saldo_horas_aluno_filtrado = None
    aulas_list = []
    total_horas_aulas_filtradas = timedelta()
    horas_contratadas_por_aluno_dict = {}
    total_contratado_todos_alunos_val = 0.0
    total_contratado_responsavel_logado = 0
    total_utilizado_pelo_responsavel_logado = 0
    saldo_total_horas_responsavel = 0
    user_is_gestor_profile = False
    user_is_professor_profile = False 
    user_is_responsavel_profile = False
    lista_de_alunos_para_filtro = Aluno.objects.all().order_by('nome')
    lista_de_professores_para_filtro = Professor.objects.all().order_by('user__first_name', 'user__last_name')

    if request.method == "POST": # Tentativa de Login
        username_from_form = request.POST.get('username')
        password_from_form = request.POST.get('password')
        user_type_selected = request.POST.get('user_type')

        user = authenticate(request, username=username_from_form, password=password_from_form)

        if user is not None:
            actual_user_type_matches = False
            is_responsavel = hasattr(user, 'responsavel_profiles') and user.responsavel_profiles.exists()
            is_professor = hasattr(user, 'professor_profile')
            is_gestor = is_gestor_check(user) 

            if user_type_selected == 'aluno_responsavel' and is_responsavel:
                actual_user_type_matches = True
            elif user_type_selected == 'professor' and is_professor:
                actual_user_type_matches = True
            elif user_type_selected == 'gestor' and is_gestor:
                actual_user_type_matches = True
            
            if actual_user_type_matches:
                auth_login(request, user)
                messages.success(request, "Login realizado com sucesso!")
                return redirect('home') 
            else:
                logout(request)
                type_display_name_selected = user_type_selected.replace('_', ' ').title()
                correct_roles = []
                if is_responsavel: correct_roles.append("Responsável")
                if is_professor: correct_roles.append("Professor")
                if is_gestor: correct_roles.append("Gestor")
                error_msg = f"Login falhou. Você selecionou '{type_display_name_selected}', mas seu perfil é: {', '.join(correct_roles) if correct_roles else 'não identificado'}. Por favor, selecione o tipo correto."
                messages.error(request, error_msg)
                return redirect('home')
        else:
            messages.error(request, "Usuário ou senha inválidos.")
            return redirect('home')

    # GET request: Exibir página
    aulas_list = []
    total_horas_aulas_filtradas = timedelta()
    horas_contratadas_por_aluno_dict = {}
    total_contratado_todos_alunos_val = 0.0
    total_contratado_responsavel_logado = 0
    total_utilizado_pelo_responsavel_logado = 0
    saldo_total_horas_responsavel = 0

    user_is_gestor_profile = False
    user_is_professor_profile = False 
    user_is_responsavel_profile = False

    
    lista_de_alunos_para_filtro = Aluno.objects.all().order_by('nome') # Ou filtre conforme necessário
    lista_de_professores_para_filtro = Professor.objects.all().order_by('user__first_name', 'user__last_name')

    if request.user.is_authenticated:
        user_is_gestor_profile = is_gestor_check(request.user)
        user_is_professor_profile = hasattr(request.user, 'professor_profile') # Definir aqui
        user_is_responsavel_profile = hasattr(request.user, 'responsavel_profiles') and request.user.responsavel_profiles.exists()

        aulas_queryset = Aula.objects.none()
        
        
        if user_is_gestor_profile:
            aulas_queryset = Aula.objects.all()
        elif user_is_professor_profile:
            try:
                aulas_queryset = Aula.objects.filter(professor=request.user.professor_profile)
            except Professor.DoesNotExist:
                messages.error(request, "Perfil de professor não encontrado.")
                aulas_queryset = Aula.objects.none()
        elif user_is_responsavel_profile:
            responsavel_instances = request.user.responsavel_profiles.all()
            aulas_queryset = Aula.objects.filter(
                aluno__responsavel__in=responsavel_instances,
                status_aprovacao='aprovada' 
            )

        
        data_de_str = request.GET.get('data_de')
        data_ate_str = request.GET.get('data_ate')
        aluno_id_str = request.GET.get('aluno')
        professor_id_str = request.GET.get('professor') # NOVO: Pegando o ID do professor do GET

        if data_de_str:
            try:
                data_de = datetime.strptime(data_de_str, '%Y-%m-%d').date()
                aulas_queryset = aulas_queryset.filter(data_inicio__gte=data_de)
            except ValueError:
                messages.error(request, "Formato de 'Data de' inválido.")

        if data_ate_str:
            try:
                data_ate = datetime.strptime(data_ate_str, '%Y-%m-%d').date()
                aulas_queryset = aulas_queryset.filter(data_inicio__lte=data_ate)
            except ValueError:
                messages.error(request, "Formato de 'Data até' inválido.")

        if aluno_id_str:
            try:
                aluno_id = int(aluno_id_str)
                aulas_queryset = aulas_queryset.filter(aluno__id=aluno_id)
            except ValueError:
                messages.error(request, "ID de aluno inválido para filtro.")

    
        # NOVO: Filtro por Professor
        if professor_id_str:
            if user_is_gestor_profile: # Apenas gestores podem filtrar por qualquer professor
                try:
                    professor_id = int(professor_id_str)
                    aulas_queryset = aulas_queryset.filter(professor__pk=professor_id)
                except ValueError:
                    messages.error(request, "ID de professor inválido para filtro.")
            elif user_is_professor_profile and str(request.user.professor_profile.id) != professor_id_str:
                # Impede que um professor tente filtrar aulas de outro professor
                messages.warning(request, "Você só pode visualizar suas próprias aulas.")
                # O queryset já está filtrado para o professor logado, então não precisamos fazer nada
                # Se ele tentar filtrar por outro ID, o filtro já estará aplicado corretamente

         # Ordenação e prefetch de objetos relacionados para otimização
        aulas_queryset = aulas_queryset.select_related('disciplina', 'aluno', 'professor__user').order_by('-data_inicio', '-hora_inicio')
        horas_contratadas_aluno_filtrado = None
        horas_utilizadas_aluno_filtrado = None
        saldo_horas_aluno_filtrado = None


        if aluno_id_str:
            try:
                aluno_filtrado = Aluno.objects.get(pk=int(aluno_id_str))

                # ① horas contratadas (somatório dos pacotes do responsável)
                horas_contratadas_aluno_filtrado = aluno_filtrado.horas_contratadas()

                # ② horas efetivamente utilizadas (apenas aulas aprovadas)
                horas_utilizadas_aluno_filtrado = aluno_filtrado.horas_utilizadas()

                # ③ saldo
                saldo_horas_aluno_filtrado = (
                    horas_contratadas_aluno_filtrado - horas_utilizadas_aluno_filtrado
                )
            except (ValueError, Aluno.DoesNotExist):
                messages.error(request, "Aluno não encontrado para calcular horas.")


         # Cálculo do total de horas das aulas filtradas
        for aula_instance in aulas_queryset:
            aula_instance.duracao_calculada = 0.0
            if aula_instance.hora_inicio and aula_instance.hora_fim and aula_instance.data_inicio:
                dia_para_calculo = aula_instance.data_inicio
                try:
                    datetime_inicio = datetime.combine(dia_para_calculo, aula_instance.hora_inicio)
                    datetime_fim = datetime.combine(dia_para_calculo, aula_instance.hora_fim)
                    if datetime_fim > datetime_inicio:
                        duracao_aula_timedelta = datetime_fim - datetime_inicio
                        
                        # A soma só considera aulas aprovadas para responsáveis, mas todas para gestores e o próprio professor
                        if aula_instance.status_aprovacao == 'aprovada' or \
                           user_is_gestor_profile or \
                           (user_is_professor_profile and hasattr(request.user, 'professor_profile') and aula_instance.professor == request.user.professor_profile):
                            total_horas_aulas_filtradas += duracao_aula_timedelta
                        
                        aula_instance.duracao_calculada = round(duracao_aula_timedelta.total_seconds() / 3600, 2)
                except TypeError:
                    aula_instance.duracao_calculada = 0.0
            aulas_list.append(aula_instance)


        # Cálculo de horas contratadas e utilizadas

        for aluno_obj in Aluno.objects.all(): 
            try:
                horas_aluno_contratadas = aluno_obj.horas_contratadas() 
                horas_contratadas_por_aluno_dict[aluno_obj.nome] = float(horas_aluno_contratadas if horas_aluno_contratadas is not None else 0.0)
            except Exception: 
                horas_contratadas_por_aluno_dict[aluno_obj.nome] = 0.0
        total_contratado_todos_alunos_val = sum(horas_contratadas_por_aluno_dict.values())
        
        if user_is_responsavel_profile:
            responsavel_instances = request.user.responsavel_profiles.all()
            
            for resp_instance in responsavel_instances:
                
                soma_pacotes_resp = sum(pacote.horas_contratadas for pacote in resp_instance.pacotes_hora.all() if isinstance(pacote.horas_contratadas, (int, float)))
                total_contratado_responsavel_logado += soma_pacotes_resp
            
            alunos_do_responsavel_logado = Aluno.objects.filter(responsavel__in=responsavel_instances)
            for aluno_resp in alunos_do_responsavel_logado:
                horas_usadas_aluno = aluno_resp.horas_utilizadas() 
                if isinstance(horas_usadas_aluno, (int, float)): 
                    total_utilizado_pelo_responsavel_logado += horas_usadas_aluno
                else:
                    
                    print(f"AVISO: Aluno ID {aluno_resp.id} - horas_utilizadas() retornou {type(horas_usadas_aluno)} em vez de um número.")
            
            saldo_total_horas_responsavel = total_contratado_responsavel_logado - total_utilizado_pelo_responsavel_logado

    context = {
        'aulas': aulas_list,
        'todos_alunos': lista_de_alunos_para_filtro, 
        'todos_professores': lista_de_professores_para_filtro, # NOVO: Para o filtro de professor no template
        'total_horas_aulas_filtradas': round(total_horas_aulas_filtradas.total_seconds() / 3600, 2),
        'horas_contratadas_por_aluno_json': json.dumps(horas_contratadas_por_aluno_dict),
        'total_contratado_todos_alunos_json': json.dumps(total_contratado_todos_alunos_val),
        'user_is_gestor': user_is_gestor_profile,
        'user_is_professor': user_is_professor_profile, 
        'total_contratado_responsavel': total_contratado_responsavel_logado if user_is_responsavel_profile else None,
        'total_utilizado_responsavel': total_utilizado_pelo_responsavel_logado if user_is_responsavel_profile else None,
        'saldo_horas_responsavel': saldo_total_horas_responsavel if user_is_responsavel_profile else None,
        'request': request, # Passar o request para o template é útil para manter os filtros selecionados
        'selected_aluno': request.GET.get('aluno', ''), # Para manter o aluno selecionado no filtro
        'selected_professor': request.GET.get('professor', ''), # Para manter o professor selecionado no filtro
        'selected_data_de': request.GET.get('data_de', ''), # Para manter a data de selecionada no filtro
        'selected_data_ate': request.GET.get('data_ate', ''), # Para manter a data até selecionada no filtro
        'user_is_gestor_profile': user_is_gestor_profile,  # alias p/ template
        'horas_contratadas_aluno_filtrado': horas_contratadas_aluno_filtrado,
        'horas_utilizadas_aluno_filtrado': horas_utilizadas_aluno_filtrado,
        'saldo_horas_aluno_filtrado': saldo_horas_aluno_filtrado,
        }
    return render(request, 'home.html', context)
    

@login_required
def add_aula(request):
    is_logged_user_gestor = is_gestor_check(request.user)
    is_logged_user_professor = hasattr(request.user, 'professor_profile')

    if not (is_logged_user_gestor or is_logged_user_professor):
        raise PermissionDenied("Você não tem permissão para adicionar aulas.")

    if request.method == 'POST':
        form = AddAulaForm(request.POST)
        
        if is_logged_user_professor and not is_logged_user_gestor:
            post_data = request.POST.copy()
            post_data['professor'] = request.user.pk
            form = AddAulaForm(post_data)

        if form.is_valid():
            aula_instance = form.save(commit=False)
            
            if is_logged_user_gestor:
                aula_instance.status_aprovacao = 'aprovada'
            else: 
                aula_instance.status_aprovacao = 'pendente'
            
            
            if is_logged_user_professor and not is_logged_user_gestor:
                aula_instance.professor = request.user.professor_profile

            aula_instance.save()
            form.save_m2m() 
            messages.success(request, f"Aula cadastrada com status '{aula_instance.get_status_aprovacao_display()}'!")
            return redirect('home')
        else:
            messages.error(request, "Erro ao cadastrar aula. Verifique os dados do formulário.")
    else: 
        form = AddAulaForm()
        if is_logged_user_professor and not is_logged_user_gestor:
            form.fields['professor'].initial = request.user.professor_profile
            form.fields['professor'].widget = forms.HiddenInput()
            form.fields['professor'].required = False # Torna não obrigatório no HTML, pois será preenchido

    return render(request, 'uniescolar/add_aula.html', {'form': form})


@login_required
def update_aula_view(request, aula_id):
    aula = get_object_or_404(Aula, id=aula_id)
    user = request.user

    is_gestor = is_gestor_check(user)
    is_professor_of_aula = hasattr(user, 'professor_profile') and aula.professor == user.professor_profile

    # Lógica de permissão para edição
    can_edit = False
    if is_gestor:
        can_edit = True 
    elif is_professor_of_aula and aula.status_aprovacao == 'pendente':
        can_edit = True # Professor pode editar SE a aula for dele E estiver pendente
    
    if not can_edit:
        messages.error(request, "Você não tem permissão para editar esta aula ou o status da aula não permite edição por você.")
        return redirect('detalhe_aula', id=aula.id) 

    
    if request.method == 'POST':
        form = AddAulaForm(request.POST, instance=aula)
        if form.is_valid():
            aula_editada = form.save(commit=False)

            if is_gestor:
                # Gestor pode mudar o status
                if 'salvar_e_aprovar' in request.POST:
                    aula_editada.status_aprovacao = 'aprovada'
                    messages.success(request, f"Aula ID {aula_editada.id} editada e APROVADA!")
                elif 'rejeitar_aula_action' in request.POST: 
                    aula_editada.status_aprovacao = 'rejeitada'
                    messages.success(request, f"Aula ID {aula_editada.id} editada e REJEITADA!")
                elif 'salvar_pendente' in request.POST:
                    aula_editada.status_aprovacao = 'pendente' 
                    messages.success(request, f"Aula ID {aula_editada.id} editada e mantida PENDENTE.")
                else: 
                    if not ('salvar_e_aprovar' in request.POST or 'rejeitar_aula_action' in request.POST or 'salvar_pendente' in request.POST):
                         aula_editada.status_aprovacao = aula.status_aprovacao 
                    messages.success(request, f"Aula ID {aula_editada.id} editada.")

            else: # Se for professor editando
                aula_editada.status_aprovacao = 'pendente'                 
                if hasattr(user, 'professor_profile'):
                    aula_editada.professor = user.professor_profile
                messages.success(request, f"Suas edições para a Aula ID {aula_editada.id} foram salvas e estão PENDENTES de aprovação.")
            
            aula_editada.save()
            form.save_m2m() 
            return redirect('detalhe_aula', id=aula_editada.id) 
        else:
            messages.error(request, "Não foi possível salvar as alterações. Verifique os erros no formulário.")
    else: # GET request
        form = AddAulaForm(instance=aula)
        if not is_gestor and 'professor' in form.fields:
            form.fields['professor'].widget = forms.HiddenInput()
            # Ou, se quiser mostrar mas não permitir edição:
            # form.fields['professor'].disabled = True

    context = {
        'form': form,
        'aula': aula,
        'page_title': f"Editar Aula",
        'is_gestor': is_gestor, 
    }
    # Use o mesmo template de edição, ele será adaptado com base em 'is_gestor'
    return render(request, 'uniescolar/editar_aula_gestor.html', context)


@login_required
@user_passes_test(is_gestor_check, login_url='home') 
@require_POST 
def aprovar_aula_view(request, aula_id): # Certifique-se que esta view existe
    aula = get_object_or_404(Aula, id=aula_id)
    if aula.status_aprovacao == 'pendente':
        aula.status_aprovacao = 'aprovada'
        aula.save()
        messages.success(request, f"Aula ID {aula.id} ({aula.disciplina}) APROVADA com sucesso.")
    else:
        messages.warning(request, f"Aula ID {aula.id} não estava pendente ou já foi processada.")
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
@user_passes_test(is_gestor_check, login_url='home')
@require_POST
def rejeitar_aula_view(request, aula_id):
    aula = get_object_or_404(Aula, id=aula_id)
    if aula.status_aprovacao == 'pendente':
        aula.status_aprovacao = 'rejeitada'
        aula.save()
        messages.success(request, f"Aula ID {aula.id} ({aula.disciplina}) REJEITADA com sucesso.")
    else:
        messages.warning(request, f"Aula ID {aula.id} não estava pendente ou já foi processada.")
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
def aula_detail_view(request, id):
    aula_instance = get_object_or_404(Aula.objects.select_related('disciplina', 'aluno', 'professor__user'), id=id)
    
    user_can_view = False
    user_is_gestor = is_gestor_check(request.user)
    user_is_professor_of_aula = hasattr(request.user, 'professor_profile') and aula_instance.professor == request.user.professor_profile
    user_is_responsavel_of_aluno = False
    if hasattr(request.user, 'responsavel_profiles'):
        if aula_instance.aluno.responsavel in request.user.responsavel_profiles.all():
            user_is_responsavel_of_aluno = True

    if user_is_gestor:
        user_can_view = True
    elif user_is_professor_of_aula:
        user_can_view = True
    elif user_is_responsavel_of_aluno and aula_instance.status_aprovacao == 'aprovada':
        user_can_view = True
    
    if not user_can_view:
        messages.error(request, "Você não tem permissão para ver detalhes desta aula ou a aula não está aprovada.")
        return redirect('home')

    if not hasattr(aula_instance, 'duracao_calculada'):
        aula_instance.duracao_calculada = 0.0
        if aula_instance.hora_inicio and aula_instance.hora_fim:
            dia_para_calculo = aula_instance.data_inicio if aula_instance.data_inicio else date.today()
            try:
                datetime_inicio = datetime.combine(dia_para_calculo, aula_instance.hora_inicio)
                datetime_fim = datetime.combine(dia_para_calculo, aula_instance.hora_fim)
                if datetime_fim > datetime_inicio:
                    aula_instance.duracao_calculada = round((datetime_fim - datetime_inicio).total_seconds() / 3600, 2)
            except TypeError:
                pass
            
    return render(request,'aula.html',{'aula':aula_instance})


@login_required
@require_POST # Garante que esta view só aceite requisições POST
def excluir_aula(request, aula_id):
    aula = get_object_or_404(Aula, id=aula_id)
    can_delete = False
    user_is_gestor = is_gestor_check(request.user)
    
    # Verifica se o usuário logado é o professor da aula
    user_is_professor_of_aula = False
    if hasattr(request.user, 'professor_profile') and aula.professor == request.user.professor_profile:
        user_is_professor_of_aula = True
    if user_is_gestor:
        can_delete = True
    elif user_is_professor_of_aula and aula.status_aprovacao == 'pendente':        
        can_delete = True
    
    if not can_delete:
        messages.error(request, 'Você não tem permissão para excluir esta aula ou o status da aula não permite a exclusão.')        
        return redirect('detalhe_aula', id=aula_id) 
    try:
        aula_disciplina_nome = aula.disciplina.nome 
        aula.delete()
        messages.success(request, f"Aula de '{aula_disciplina_nome}' excluída com sucesso!")
    except Exception as e:
        messages.error(request, f"Ocorreu um erro ao tentar excluir a aula: {e}")        
        return redirect('detalhe_aula', id=aula_id) 

    return redirect('home')


def logout_user(request):
    logout(request)
    messages.success(request, "Logout realizado com sucesso!")
    return redirect('home')


def register_user(request):
    if request.method == 'POST': 
        user_form = SignUpForm(request.POST)
        if user_form.is_valid(): 
            usuario_instance = user_form.save(commit=False)
            usuario_instance.senha = make_password(user_form.cleaned_data['senha']) 
            usuario_instance.save()
            messages.success(request, 'Cadastro (modelo Usuário) realizado. Para login com perfis, um admin precisa criar seu usuário Django e vincular o perfil.')
            return redirect('home') 
        else:
            
            messages.error(request, 'Erro no formulário de cadastro. Verifique os dados.')
            return render(request, "register.html", {'user_form': user_form})
    else:
        user_form = SignUpForm()
    return render(request, "register.html", {'user_form': user_form})

# def aula_detail(request,id):
#     if request.user.is_authenticated:
#         aulas=Aula.objects.get(id=id) # Buscar objeto pelo id
#         return render (request,'aula_detail.html',{'aula_detail':aulas})
#     else:
#         messages.error(request,'Você precisa estar logado')
#         return redirect('home')