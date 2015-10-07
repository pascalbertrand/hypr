import pytest
from hypr import Hypr
from test_tools import fltr_provider_factory


@pytest.fixture(scope='class')
def app(request):

    app = Hypr()

    for provider, urls in request.cls.providers.items():

        if isinstance(provider, str):
            provider = getattr(
                request.module,
                provider,
                type(provider, (fltr_provider_factory(),), {})
            )

        if not isinstance(urls, tuple):
            urls = urls,
        app.router.add_provider(provider, *urls)

    app.propagate()
    return app
