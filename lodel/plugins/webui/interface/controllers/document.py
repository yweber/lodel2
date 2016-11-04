from .base import get_response


def show_document(request):
    template_vars = {'id': request.url_args['id']}
    return get_response('documents/show.html', tpl_vars=template_vars)