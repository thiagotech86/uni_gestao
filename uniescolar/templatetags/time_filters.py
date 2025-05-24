from django import template
import math

register = template.Library()

@register.filter(name='format_hours_minutes')
def format_hours_minutes(value):
    """
    Formata um valor decimal de horas (float ou string conversível) 
    para uma string no formato 'XhYYm' ou '-XhYYm'.
    Exemplos:
    2.5  -> "2h30"
    3.0  -> "3h00"
    0.75 -> "0h45"
    None -> "0h00"
    -2.5 -> "-2h30"
    """
    if value is None:
        return "0h00"
    try:
        decimal_hours = float(value)

        if math.isnan(decimal_hours) or math.isinf(decimal_hours):
            return "---" # Representação para valores não numéricos como NaN ou Infinito

        sign = "-" if decimal_hours < 0 else ""
        abs_decimal_hours = abs(decimal_hours)
        
        hours = int(abs_decimal_hours)
        # Calcula os minutos a partir da parte fracionária das horas absolutas
        minutes_float = (abs_decimal_hours - hours) * 60
        minutes = int(round(minutes_float)) # Arredonda para o minuto inteiro mais próximo
        
        # Ajusta caso o arredondamento dos minutos resulte em 60
        if minutes == 60:
            hours += 1
            minutes = 0
            
        return f"{sign}{hours}h{minutes:02d}" # Formata os minutos com zero à esquerda se necessário
        
    except (ValueError, TypeError):
        # Retorna "0h00" se o valor não puder ser convertido para float
        return "0h00"
