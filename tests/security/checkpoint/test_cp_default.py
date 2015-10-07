from hypr import Provider, checkpoint, abort
import json


class Root(Provider):

    @checkpoint
    def default_checkpoint(self, value):
        if value == 1:
            abort(403)
        
    def get(self, value):
        return value


class TestDefaultCheckpoint:

    providers = {
        'Root': '/root/<int:value>',
    }

    def test_accept_0(self, app):

        with app.test_client() as client:
            vtt = client.get('/root/0')
            assert vtt.status == 200

    def test_reject_0(self, app):

        with app.test_client() as client:
            vtt = client.get('/root/1')
            assert vtt.status == 403
