from django.template import Context, Template


def render_from_string(content, context=None):
    if isinstance(context, dict):
        context = Context(context)

    tpl = Template(content)

    return tpl.render(context or Context())
