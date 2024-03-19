from notmm.lib.wsgiapp import render_to_response

def index(request, **kwargs):
    #locale = request.environ['user.locale']

    return render_to_response(request, **kwargs)
