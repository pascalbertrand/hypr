import json
import pytest
from hypr import Hypr, Provider


class CustomProvider(Provider):

    def get(self, value=None):

        if value == 'resp':
            return 'ok'

        elif value == 'resp_status':
            return 'ok', 201

        elif value == 'resp_header':
            return 'ok', {'X-test-header': 'ok'}

        elif value == 'resp_status_header':
            return 'ok', 201, {'X-test-header': 'ok'}

        return None


class TestRuleDefinition:

    providers = {
        CustomProvider: ('/', '/<any(resp, resp_status, resp_header, resp_status_header):value>')
    }

    def test_resp(self, app):

        with app.test_client() as client:

            resp = client.get('/resp')
            assert json.loads(resp.text) == 'ok'
            assert resp.status == 200

    def test_resp_status(self, app):

        with app.test_client() as client:

            resp = client.get('/resp_status')
            assert json.loads(resp.text) == 'ok'
            assert resp.status == 201

    def test_resp_header(self, app):

        with app.test_client() as client:

            resp = client.get('/resp_header')
            assert json.loads(resp.text) == 'ok'
            assert resp.status == 200
            assert resp.headers['X-TEST-HEADER'] == 'ok'

    def test_resp_status_header(self, app):

        with app.test_client() as client:

            resp = client.get('/resp_status_header')
            assert json.loads(resp.text) == 'ok'
            assert resp.status == 201
            assert resp.headers['X-TEST-HEADER'] == 'ok'


    def test_resp_is_none(self, app):

        with app.test_client() as client:

            resp = client.get('/')
            assert resp.status == 500
