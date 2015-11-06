import pytest

from hypr import Hypr, Provider, checkpoint, abort


class MyProvider(Provider):

    value = 0

    @checkpoint(priority=0)
    def high_priority(self):
        self.value = 1

    @checkpoint
    def default_priority(self):
        self.value += 1

    @checkpoint(priority=100)
    def low_priority(self):
        if self.value != 2:
            abort(401)

    def get(self):
        return 'ok'


@pytest.fixture(scope='class')
def app():

    app = Hypr()
    app.router.add_provider(MyProvider, '/test')
    return app


class TestCheckpointPriority:

    def test_expected(self, app):

        with app.test_client() as client:

            vtt = client.get('/test')
            assert vtt.status == 200
