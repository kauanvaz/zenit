import markdown as md
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='markdown')
def markdown_format(text):
    """
    Filtro para renderizar markdown em HTML.
    """
    if not text:
        return ''
    
    # Renderiza markdown e marca como seguro para o Django
    # 'extra' ativa tabelas, blocos de código, etc.
    # 'nl2br' transforma quebras de linha em <br>
    return mark_safe(md.markdown(text, extensions=['extra', 'nl2br']))
