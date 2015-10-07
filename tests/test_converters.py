import json
import pytest
from hypr import Hypr, Provider


class TestUnknownConverter:

    def test_unknown_provider(self, app):
        
        with pytest.raises(LookupError) as err:
            app.router.add_provider(Provider, '/<unknown:value>')

        assert 'The converter \'unknown\' does not exist' in str(err)


class TestStringConverter:

    providers = {
        'Default': '/default/<string:value>',
        'Length': '/length/<string(length=4):value>',
        'MinLength': '/minlength/<string(minlength=2):value>',
        'MaxLength': '/maxlength/<string(maxlength=4):value>',
        'MinMax': '/minmax/<string(minlength=2, maxlength=4):value>',
    }

    def test_0(self, app):

        with app.test_client() as client:

            resp = client.get('/default/test')
            assert json.loads(resp.text) == 'test'
            assert resp.status == 200

    def test_1(self, app):

        with app.test_client() as client:

            resp = client.get('/default/1')
            assert json.loads(resp.text) == '1'
            assert resp.status == 200

    def test_2(self, app):

        with app.test_client() as client:

            resp = client.get('/default/foo/bar')
            assert resp.status == 404

    def test_3(self, app):

        with app.test_client() as client:

            resp = client.get('/length/test')
            assert json.loads(resp.text) == 'test'
            assert resp.status == 200

    def test_4(self, app):

        with app.test_client() as client:

            resp = client.get('/length/1')
            assert resp.status == 404

    def test_5(self, app):

        with app.test_client() as client:

            resp = client.get('/length/foobar')
            assert resp.status == 404

    def test_6(self, app):

        with app.test_client() as client:

            resp = client.get('/minlength/test')
            assert json.loads(resp.text) == 'test'
            assert resp.status == 200

    def test_7(self, app):

        with app.test_client() as client:

            resp = client.get('/minlength/1')
            assert resp.status == 404

    def test_8(self, app):

        with app.test_client() as client:

            resp = client.get('/minlength/foobar')
            assert json.loads(resp.text) == 'foobar'
            assert resp.status == 200

    def test_9(self, app):

        with app.test_client() as client:

            resp = client.get('/maxlength/test')
            assert json.loads(resp.text) == 'test'
            assert resp.status == 200

    def test_10(self, app):

        with app.test_client() as client:

            resp = client.get('/maxlength/1')
            assert json.loads(resp.text) == '1'
            assert resp.status == 200

    def test_11(self, app):

        with app.test_client() as client:

            resp = client.get('/maxlength/foobar')
            assert resp.status == 404

    def test_12(self, app):

        with app.test_client() as client:

            resp = client.get('/minmax/test')
            assert json.loads(resp.text) == 'test'
            assert resp.status == 200

    def test_13(self, app):

        with app.test_client() as client:

            resp = client.get('/minmax/1')
            assert resp.status == 404

    def test_14(self, app):

        with app.test_client() as client:

            resp = client.get('/minmax/foobar')
            assert resp.status == 404


class TestPathConverter:

    providers = {
        'Default': '/<path:value>',
    }

    def test_0(self, app):

        with app.test_client() as client:

            resp = client.get('/test')
            assert resp.status == 200
            assert json.loads(resp.text) == 'test'

    def test_1(self, app):

        with app.test_client() as client:

            resp = client.get('/1')
            assert resp.status == 200
            assert json.loads(resp.text) == '1'

    def test_2(self, app):

        with app.test_client() as client:

            resp = client.get('/foo/bar')
            assert resp.status == 200
            assert json.loads(resp.text) == 'foo/bar'


class TestIntegerConverter:

    providers = {
        'Default': '/default/<int:value>',
        'Min': '/min/<int(min=4):value>',
        'Max': '/max/<int(max=3):value>',
        'Digit': '/digit/<int(fixed_digits=4):value>',
    }

    def test_0(self, app):

        with app.test_client() as client:

            resp = client.get('/default/test')
            assert resp.status == 404

    def test_1(self, app):

        with app.test_client() as client:

            resp = client.get('/default/1')
            assert resp.status == 200
            assert json.loads(resp.text) == 1

    def test_2(self, app):

        with app.test_client() as client:

            resp = client.get('/default/1.0')
            assert resp.status == 404

    def test_3(self, app):

        with app.test_client() as client:

            resp = client.get('/min/1')
            assert resp.status == 404

    def test_4(self, app):

        with app.test_client() as client:

            resp = client.get('/min/4')
            assert resp.status == 200
            assert json.loads(resp.text) == 4

    def test_5(self, app):

        with app.test_client() as client:

            resp = client.get('/max/1')
            assert resp.status == 200
            assert json.loads(resp.text) == 1

    def test_6(self, app):

        with app.test_client() as client:

            resp = client.get('/max/4')
            assert resp.status == 404

    def test_7(self, app):

        with app.test_client() as client:

            resp = client.get('/digit/1')
            assert resp.status == 404

    def test_8(self, app):

        with app.test_client() as client:

            resp = client.get('/digit/4444')
            assert resp.status == 200
            assert json.loads(resp.text) == 4444

    def test_9(self, app):

        with app.test_client() as client:

            resp = client.get('/digit/55555')
            assert resp.status == 404

    def test_10(self, app):

        with app.test_client() as client:

            resp = client.get('/digit/0001')
            assert resp.status == 200
            assert json.loads(resp.text) == 1



class TestFloatConverter:

    providers = {
        'Default': '/default/<float:value>',
        'Min': '/min/<float(min=4):value>',
        'Max': '/max/<float(max=3.1):value>',
    }

    def test_0(self, app):

        with app.test_client() as client:

            resp = client.get('/default/test')
            assert resp.status == 404

    def test_1(self, app):

        with app.test_client() as client:

            resp = client.get('/default/1.0')
            assert resp.status == 200
            assert json.loads(resp.text) == 1

    def test_2(self, app):

        with app.test_client() as client:

            resp = client.get('/default/1')
            assert resp.status == 404

    def test_3(self, app):

        with app.test_client() as client:

            resp = client.get('/min/1.0')
            assert resp.status == 404

    def test_4(self, app):

        with app.test_client() as client:

            resp = client.get('/min/4.1')
            assert resp.status == 200
            assert json.loads(resp.text) == 4.1

    def test_5(self, app):

        with app.test_client() as client:

            resp = client.get('/max/.9')
            assert resp.status == 200
            assert json.loads(resp.text) == 0.9

    def test_6(self, app):

        with app.test_client() as client:

            resp = client.get('/max/3.11')
            assert resp.status == 404


class TestUUIDConverter:

    providers = {
        'Default': '/<uuid:value>',
    }

    def test_0(self, app):

        with app.test_client() as client:

            resp = client.get('/de305d5475b4431babd2eb6b9e546014')
            assert resp.status == 404

    def test_1(self, app):

        with app.test_client() as client:

            resp = client.get('/de305d54-75b4-431b-abd2-eb6b9e546014')
            assert resp.status == 200
            assert json.loads(resp.text) == 'de305d54-75b4-431b-abd2-eb6b9e546014'


class TestAnyConverter:

    providers = {
        'Default': '/<any(foo, bar):value>',
    }

    def test_0(self, app):

        with app.test_client() as client:

            resp = client.get('/foo')
            assert resp.status == 200
            assert json.loads(resp.text) == 'foo'

    def test_1(self, app):

        with app.test_client() as client:

            resp = client.get('/bar')
            assert resp.status == 200
            assert json.loads(resp.text) == 'bar'

    def test_2(self, app):

        with app.test_client() as client:

            resp = client.get('/baz')
            assert resp.status == 404

