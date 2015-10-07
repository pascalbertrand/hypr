from hypr import Provider, checkpoint, filter, request, abort


class ProviderTemplate(Provider):

    def get(self, value=None):
        if value is None:
            return {self.name: 'ok'}
        return value


def cp_provider_factory(scope=None):

    # Return a provider with a specified scope rejecting all request with a
    # 403 error if the value of the eponym segments in the URL is 1

    class CPProviderTemplate(ProviderTemplate):

        @checkpoint(scope)
        def custom_cp(self, value=None):
            if value == 1:
                abort(403)

    return CPProviderTemplate


def fltr_provider_factory(key=None, scope=None, requires=None):

    class ProviderTemplate(Provider):

        @filter(key, scope, requires)
        def mandatory_filter(self, value):
            return value

        def get(self, value=None):
            return request.m_filters

    return ProviderTemplate

