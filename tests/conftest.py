import pytest
from hypr import Hypr, Provider
from test_tools import ProviderTemplate


@pytest.fixture(scope='class')
def app(request):

    app = Hypr()

    for provider, urls in getattr(request.cls, 'providers', {}).items():

        if isinstance(provider, str):
            provider = getattr(
                request.module,
                provider,
                type(provider, (ProviderTemplate,), {})
            )

        if not isinstance(urls, tuple):
            urls = urls,

        app.router.add_provider(provider, *urls)

    app.propagate()
    return app
