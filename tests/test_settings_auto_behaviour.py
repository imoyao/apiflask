import pytest
from flask.views import MethodView
from openapi_spec_validator import validate_spec

from .schemas import FooSchema
from .schemas import QuerySchema
from apiflask import APIBlueprint
from apiflask import auth_required
from apiflask import doc
from apiflask import input
from apiflask.security import HTTPBasicAuth


def test_auto_tags(app, client):
    bp = APIBlueprint('foo', __name__)
    app.config['AUTO_TAGS'] = False

    @bp.get('/')
    def foo():
        pass

    app.register_blueprint(bp)
    rv = client.get('/openapi.json')
    assert rv.status_code == 200
    validate_spec(rv.json)
    assert rv.json['tags'] == []
    assert 'tags' not in rv.json['paths']['/']['get']


@pytest.mark.parametrize('config_value', [True, False])
def test_auto_path_summary(app, client, config_value):
    app.config['AUTO_OPERATION_SUMMARY'] = config_value

    @app.get('/foo')
    def foo():
        pass

    @app.get('/bar')
    def get_bar():
        pass

    @app.get('/baz')
    def get_baz():
        """Baz Summary"""
        pass

    @app.get('/spam')
    def get_spam():
        """Spam Summary

        some description
        """
        pass

    @app.get('/eggs')
    @doc(summary='Eggs from doc decortor')
    def get_eggs():
        """Eggs Summary

        some description
        """
        pass

    rv = client.get('/openapi.json')
    assert rv.status_code == 200
    validate_spec(rv.json)
    if config_value:
        assert rv.json['paths']['/foo']['get']['summary'] == 'Foo'
        assert rv.json['paths']['/bar']['get']['summary'] == 'Get Bar'
        assert rv.json['paths']['/baz']['get']['summary'] == 'Baz Summary'
        assert rv.json['paths']['/spam']['get']['summary'] == 'Spam Summary'
    else:
        assert 'summary' not in rv.json['paths']['/foo']['get']
        assert 'summary' not in rv.json['paths']['/bar']['get']
        assert 'summary' not in rv.json['paths']['/baz']['get']
        assert 'summary' not in rv.json['paths']['/spam']['get']
    assert rv.json['paths']['/eggs']['get']['summary'] == 'Eggs from doc decortor'


@pytest.mark.parametrize('config_value', [True, False])
def test_auto_path_summary_with_methodview(app, client, config_value):
    app.config['AUTO_OPERATION_SUMMARY'] = config_value

    @app.route('/foo')
    class Foo(MethodView):
        def get(self):
            pass

        def post(self):
            """Post Summary"""
            pass

        def delete(self):
            """Delete Summary

            some description
            """
            pass

        @doc(summary='Put from doc decortor')
        def put(self):
            """Delete Summary

            some description
            """
            pass

    rv = client.get('/openapi.json')
    assert rv.status_code == 200
    validate_spec(rv.json)
    if config_value:
        assert rv.json['paths']['/foo']['get']['summary'] == 'Get Foo'
        assert rv.json['paths']['/foo']['post']['summary'] == 'Post Summary'
        assert rv.json['paths']['/foo']['delete']['summary'] == 'Delete Summary'
    else:
        assert 'summary' not in rv.json['paths']['/foo']['get']
        assert 'summary' not in rv.json['paths']['/foo']['post']
        assert 'summary' not in rv.json['paths']['/foo']['delete']
    assert rv.json['paths']['/foo']['put']['summary'] == 'Put from doc decortor'


@pytest.mark.parametrize('config_value', [True, False])
def test_auto_path_description(app, client, config_value):
    app.config['AUTO_OPERATION_DESCRIPTION'] = config_value

    @app.get('/foo')
    def get_foo():
        """Foo

        some description for foo
        """
        pass

    @app.get('/bar')
    @doc(description='bar from doc decortor')
    def get_bar():
        """Bar

        some description for bar
        """
        pass

    @app.route('/baz')
    class Baz(MethodView):
        def get(self):
            """Baz

            some description for baz
            """
            pass

        @doc(description='post from doc decortor')
        def post(self):
            """Baz

            some description for baz
            """
            pass

    rv = client.get('/openapi.json')
    assert rv.status_code == 200
    validate_spec(rv.json)
    if config_value:
        assert rv.json['paths']['/foo']['get']['description'] == 'some description for foo'
        assert rv.json['paths']['/baz']['get']['description'] == 'some description for baz'
    else:
        assert 'description' not in rv.json['paths']['/foo']['get']
        assert 'description' not in rv.json['paths']['/baz']['get']
    assert rv.json['paths']['/bar']['get']['description'] == 'bar from doc decortor'
    assert rv.json['paths']['/baz']['post']['description'] == 'post from doc decortor'


@pytest.mark.parametrize('config_value', [True, False])
def test_auto_200_response_for_bare_views(app, client, config_value):
    app.config['AUTO_200_RESPONSE'] = config_value

    @app.get('/foo')
    def foo():
        pass

    @app.route('/bar')
    class Bar(MethodView):
        def get(self):
            pass

        def post(self):
            pass

    @app.route('/baz')
    class Baz(MethodView):
        def get(self):
            pass

        @input(FooSchema)
        def post(self):
            pass

    rv = client.get('/openapi.json')
    assert rv.status_code == 200
    validate_spec(rv.json)
    assert bool('/foo' in rv.json['paths']) is config_value
    assert bool('/bar' in rv.json['paths']) is config_value
    assert '/baz' in rv.json['paths']
    assert bool('get' in rv.json['paths']['/baz']) is config_value
    assert 'post' in rv.json['paths']['/baz']


@pytest.mark.parametrize('config_value', [True, False])
def test_auto_200_response_for_no_output_views(app, client, config_value):
    app.config['AUTO_200_RESPONSE'] = config_value

    @app.get('/foo')
    @input(QuerySchema, 'query')
    def foo():
        pass

    @app.route('/bar')
    class Bar(MethodView):
        @input(QuerySchema, 'query')
        def get(self):
            pass

    rv = client.get('/openapi.json')
    assert rv.status_code == 200
    validate_spec(rv.json)
    assert '/foo' in rv.json['paths']
    assert '/bar' in rv.json['paths']
    assert bool('200' in rv.json['paths']['/foo']['get']['responses']) is config_value
    assert bool('200' in rv.json['paths']['/bar']['get']['responses']) is config_value


@pytest.mark.parametrize('config_value', [True, False])
def test_auto_validation_error_response(app, client, config_value):
    app.config['AUTO_VALIDATION_ERROR_RESPONSE'] = config_value

    @app.post('/foo')
    @input(FooSchema)
    def foo():
        pass

    rv = client.get('/openapi.json')
    assert rv.status_code == 200
    validate_spec(rv.json)
    assert bool('400' in rv.json['paths']['/foo']['post']['responses']) is config_value
    if config_value:
        assert 'ValidationError' in rv.json['components']['schemas']
        assert '#/components/schemas/ValidationError' in \
            rv.json['paths']['/foo']['post']['responses']['400'][
                'content']['application/json']['schema']['$ref']


@pytest.mark.parametrize('config_value', [True, False])
def test_auto_auth_error_response(app, client, config_value):
    app.config['AUTO_AUTH_ERROR_RESPONSE'] = config_value
    auth = HTTPBasicAuth()

    @app.post('/foo')
    @auth_required(auth)
    def foo():
        pass

    rv = client.get('/openapi.json')
    assert rv.status_code == 200
    validate_spec(rv.json)
    assert bool('401' in rv.json['paths']['/foo']['post']['responses']) is config_value
    if config_value:
        assert 'HTTPError' in rv.json['components']['schemas']
        assert '#/components/schemas/HTTPError' in \
            rv.json['paths']['/foo']['post']['responses']['401'][
                'content']['application/json']['schema']['$ref']


@pytest.mark.parametrize('config_value', [True, False])
def test_auto_404_error(app, client, config_value):
    app.config['AUTO_404_RESPONSE'] = config_value

    @app.get('/foo/<int:id>')
    def foo():
        pass

    rv = client.get('/openapi.json')
    assert rv.status_code == 200
    validate_spec(rv.json)
    assert bool('404' in rv.json['paths']['/foo/{id}']['get']['responses']) is config_value
    if config_value:
        assert 'HTTPError' in rv.json['components']['schemas']
        assert '#/components/schemas/HTTPError' in \
            rv.json['paths']['/foo/{id}']['get']['responses']['404'][
                'content']['application/json']['schema']['$ref']
