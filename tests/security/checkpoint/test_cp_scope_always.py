class TestCheckpointScope:

    providers = {
        'Root': '/<int:value>'
    }

    def test_accept_1(self, app):

        with app.test_client() as client:
            vtt = client.get('/0')
            assert vtt.status == 200

    def test_reject_0(self, app):

        with app.test_client() as client:
            vtt = client.get('/1')
            assert vtt.status == 403
