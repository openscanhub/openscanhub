from django.http import HttpResponse
from django.urls import reverse
from django.template.loader import get_template



class LoginRequiredMiddleware(object):
    """
    Specially hacked middleware to make sure the user list/detail page are
    visible only to authenticated users.

    This is an ugly hack based on kobo's implementation of `users`. Updating
    kobo would be more straightforward, but that might break other modules
    that depend on kobo.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path_info = request.META["PATH_INFO"]
        # This `user/list` comes from kobo's view name for user
        kobo_user_view_url = reverse("user/list")
        if path_info.startswith(kobo_user_view_url):
            if not request.user.is_authenticated:
                template = get_template("base.html")
                context = {
                    "info_message": "Please login to view users.",
                }
                return HttpResponse(
                    template.render(context, request=request),
                    status=403)

        return self.get_response(request)
