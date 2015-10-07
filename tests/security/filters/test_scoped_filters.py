from hypr import Provider, filter
import json


class Root(Provider):

    propagation_rules = {
        'rule0': ('Resource', '/rule0'),
        'rule1': ('Resource', '/rule1'),
        'rule2': ('Resource', '/rule2'),
        'rule3': ('Resource', '/rule3')
    }

    @filter(key='always')
    def always_filter(self, value):
        return value

    @filter(key='rule0', scope='rule0')
    def rule0_filter(self, value):
        return value

    @filter(key='rule1', scope='rule1')
    def rule1_filter(self, value):
        return value

    @filter(key='multi', scope=('rule0', 'rule2'))
    def multi_filter(self, value):
        return value

    def get(self, value):
        return value


class TestScopedFilter:

    providers = {
        'Root': '/root/<int:value>',
        'Resource': '/resource'
    }

    def test_always_only(self, app):

        with app.test_client() as client:

            resp = client.get('/root/1/rule3')
            assert resp.status == 200
            assert json.loads(resp.text) == {'always': 1}

    def test_specific(self, app):

        with app.test_client() as client:

            resp = client.get('/root/1/rule1')
            assert resp.status == 200
            assert json.loads(resp.text) == {'always': 1, 'rule1': 1}


    def test_multi(self, app):

        with app.test_client() as client:

            resp = client.get('/root/1/rule2')
            assert resp.status == 200
            assert json.loads(resp.text) == {'always': 1, 'multi': 1}


    def test_multi_and_specific(self, app):

        with app.test_client() as client:

            resp = client.get('/root/1/rule0')
            assert resp.status == 200
            assert json.loads(resp.text) == {'always': 1,
                                             'multi': 1,
                                             'rule0': 1}
