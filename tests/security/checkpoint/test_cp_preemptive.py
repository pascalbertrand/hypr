import pytest
from hypr import Hypr, Provider, Response, checkpoint, abort

from test_tools import cp_provider_factory


BaseProvider = cp_provider_factory()


class Root(BaseProvider):

    def get(self):
        abort(404)


class TestCPPreempt:

    providers = {
        Root: '/<int:value>',
    }


    def test_cp_is_preemptive(self, app):

        with app.test_client() as client:
            vtt = client.get('/1')
            assert vtt.status == 403

