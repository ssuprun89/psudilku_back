from django.http import Http404


class GetObject404:
    defaults_method = ["partial_update", "update", "destroy"]

    def get_object(self):
        obj = super().get_object()
        if self.action in self.defaults_method and self.request.user.id != obj.user.id:
            raise Http404
        return obj


class GetObject404User:
    defaults_method = ["partial_update", "update", "destroy"]

    def get_object(self):
        obj = super().get_object()
        if self.action in self.defaults_method and self.request.user.id != obj.id:
            raise Http404
        return obj
