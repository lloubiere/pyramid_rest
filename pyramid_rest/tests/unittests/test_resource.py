# -*- coding: utf-8 -*-
import unittest

import mock


class TestResourceViewMapper(unittest.TestCase):

    def test_init_and_call(self):
        from pyramid_rest.resource import ResourceViewMapper

        kwargs = dict()
        view = mock.Mock()
        ctx = mock.Mock()
        req = mock.MagicMock()
        req.matchdict.keys.return_value = ('id1', 'id0', 'id3', 'id2')

        rvm = ResourceViewMapper(**kwargs)
        wrapped = rvm(view)
        result = wrapped(ctx, req)

        self.assertEqual(kwargs, rvm.kwargs)
        self.assertEqual(view.return_value, result)

        ids = req.matchdict.__getitem__.return_value

        view.assert_called_once_with(ctx, req, ids, ids, ids, ids)

        # assert that ids are sorted alphabetically
        self.assertEqual(
            mock.call('id0',),
            req.matchdict.__getitem__.call_args_list[0]
            )
        self.assertEqual(
            mock.call('id1'),
            req.matchdict.__getitem__.call_args_list[1]
            )
        self.assertEqual(
            mock.call('id2'),
            req.matchdict.__getitem__.call_args_list[2]
            )
        self.assertEqual(
            mock.call('id3'),
            req.matchdict.__getitem__.call_args_list[3]
            )


class TestResourceUtility(unittest.TestCase):

    def test_init(self):
        from pyramid_rest.resource import ResourceUtility

        config = mock.Mock()

        ru = ResourceUtility(config)

        self.assertEqual(config, ru.config)
        self.assertEqual(
            dict(
                index='GET',
                create='POST',
                show='GET',
                update='PUT',
                delete='DELETE',
                new='GET',
                edit='GET',
                ),
            ru.methods,
            )

    def test_add_sub_resource(self):
        from pyramid_rest.resource import ResourceUtility, Resource

        dad = Resource('dad')
        kid = Resource('dad.kid')

        config = mock.Mock()

        # kid is a sub resource:
        # Resource utility must defer processing until parent resource is added
        ru = ResourceUtility(config)
        ru.add_resource(kid)

        self.assertEqual({'dad.kid': kid}, ru.deferred)

        ru.add_resource(dad)

    @mock.patch('pyramid_rest.resource.functools')
    def test_add_resources_route(self, m_functools):
        from pyramid_rest.resource import (
            ResourceUtility,
            Resource,
            ResourceContext,
            )

        kid = Resource('dad.kid')
        dad = Resource('dad')

        config = mock.Mock()

        ru = ResourceUtility(config)

        ru.add_resource(dad)

        self.assertEqual({'dad': dad}, ru.resources)
        self.assertEqual({'dad': dad}, ru.parent_resources)

        self.assertEqual(
            mock.call(
                pattern='/dad/{id0}',
                name='dad_item',
                factory=m_functools.partial.return_value,
                ),
            config.add_route.call_args_list[0]
            )
        self.assertEqual(
            mock.call(
                pattern='/dad',
                name='dad',
                factory=m_functools.partial.return_value,
                ),
            config.add_route.call_args_list[1]
            )
        self.assertEqual(
            mock.call(
                pattern='/dad/new',
                name='dad_new',
                factory=m_functools.partial.return_value,
                ),
            config.add_route.call_args_list[2]
            )
        self.assertEqual(
            mock.call(
                pattern='/dad/{id0}/edit',
                name='dad_edit',
                factory=m_functools.partial.return_value,
                ),
            config.add_route.call_args_list[3]
            )

        ru.add_resource(kid)
        self.assertEqual({'dad': dad, 'dad.kid': kid}, ru.resources)
        self.assertEqual({'dad': dad}, ru.parent_resources)

        self.assertEqual(
            mock.call(
                pattern='/dad/{id0}/kid/{id1}',
                name='dad.kid_item',
                factory=m_functools.partial.return_value,
                ),
            config.add_route.call_args_list[4]
            )
        self.assertEqual(
            mock.call(
                pattern='/dad/{id0}/kid',
                name='dad.kid',
                factory=m_functools.partial.return_value,
                ),
            config.add_route.call_args_list[5]
            )
        self.assertEqual(
            mock.call(
                pattern='/dad/{id0}/kid/new',
                name='dad.kid_new',
                factory=m_functools.partial.return_value,
                ),
            config.add_route.call_args_list[6]
            )
        self.assertEqual(
            mock.call(
                pattern='/dad/{id0}/kid/{id1}/edit',
                name='dad.kid_edit',
                factory=m_functools.partial.return_value,
                ),
            config.add_route.call_args_list[7]
            )

    def test_add_resources_add_views(self):
        from pyramid_rest.resource import (
            ResourceUtility,
            Resource,
            ResourceContext,
            not_allowed_view,
            )

        dad_index = mock.Mock()
        dad_show = mock.Mock()

        kid_index = mock.Mock()
        kid_show = mock.Mock()

        kid = Resource('dad.kid')
        dad = Resource('dad')

        config = mock.Mock()

        ru = ResourceUtility(config)

        # simulate decorating methods:
        dad.index()(dad_index)
        dad.show()(dad_show)
        kid.index()(kid_index)
        kid.show()(kid_show)

        ru.add_resource(dad)
        ru.add_resource(kid)

        self.assertEqual(14, config.add_view.call_count)

        # check dad views:

        self._check_add_view(dad_index, 'GET', 'dad', config.add_view.call_args_list[0])
        self._check_add_view(dad_show, 'GET', 'dad_item', config.add_view.call_args_list[1])

        self._check_add_not_allowed(not_allowed_view, 'GET', 'dad_edit', config.add_view.call_args_list[2])
        self._check_add_not_allowed(not_allowed_view, 'GET', 'dad_new', config.add_view.call_args_list[3])
        self._check_add_not_allowed(not_allowed_view, 'POST', 'dad', config.add_view.call_args_list[4])
        self._check_add_not_allowed(not_allowed_view, 'PUT', 'dad_item', config.add_view.call_args_list[5])
        self._check_add_not_allowed(not_allowed_view, 'DELETE', 'dad_item', config.add_view.call_args_list[6])

        # check kid views:

        self._check_add_view(kid_index, 'GET', 'dad.kid', config.add_view.call_args_list[7])
        self._check_add_view(kid_show, 'GET', 'dad.kid_item', config.add_view.call_args_list[8])

        self._check_add_not_allowed(not_allowed_view, 'GET', 'dad.kid_edit', config.add_view.call_args_list[9])
        self._check_add_not_allowed(not_allowed_view, 'GET', 'dad.kid_new', config.add_view.call_args_list[10])
        self._check_add_not_allowed(not_allowed_view, 'POST', 'dad.kid', config.add_view.call_args_list[11])
        self._check_add_not_allowed(not_allowed_view, 'PUT', 'dad.kid_item', config.add_view.call_args_list[12])
        self._check_add_not_allowed(not_allowed_view, 'DELETE', 'dad.kid_item', config.add_view.call_args_list[13])

    def _check_add_view(self, view, request_method, route_name, real_call):
        from pyramid_rest.resource import ResourceViewMapper
        self.assertEqual(
            mock.call(
                view=view,
                mapper=ResourceViewMapper,
                request_method=request_method,
                route_name=route_name
                ),
            real_call,
            )

    def _check_add_not_allowed(self, view, request_method, route_name, real_call):
        from pyramid_rest.resource import ResourceViewMapper
        self.assertEqual(
            mock.call(
                view=view,
                request_method=request_method,
                route_name=route_name
                ),
            real_call,
            )

class TestNotAllowedView(unittest.TestCase):

    def test_raising_http_not_allowed(self):
        from pyramid_rest.resource import not_allowed_view, HTTPMethodNotAllowed
        self.assertRaises(HTTPMethodNotAllowed, not_allowed_view, None)


class TestResource(unittest.TestCase):

    @mock.patch('pyramid_rest.resource.functools')
    def test_init(self, m_functools):
        from pyramid_rest.resource import Resource

        r = Resource('dad')

        self.assertEqual(m_functools.partial.return_value, r.index)
        self.assertEqual(m_functools.partial.return_value, r.show)
        self.assertEqual(m_functools.partial.return_value, r.create)
        self.assertEqual(m_functools.partial.return_value, r.update)
        self.assertEqual(m_functools.partial.return_value, r.delete)
        self.assertEqual(m_functools.partial.return_value, r.new)
        self.assertEqual(m_functools.partial.return_value, r.edit)

        self.assertEqual('<Resource_dad>', r.__repr__())

    @mock.patch('pyramid_rest.resource.venusian')
    def test_decorator(self, m_venusian):
        from pyramid_rest.resource import Resource

        r = Resource('dad')

        view_index = mock.Mock()

        wrapper = r.decorator('index')
        result = wrapper(view_index)

        self.assertEqual(view_index, result)
        self.assertEqual(
            {'index': (view_index, m_venusian.attach.return_value)},
            r.views
            )

        self.assertEqual(
            mock.call(r, r.callback),
            m_venusian.attach.call_args_list[0]
            )
        self.assertEqual(
            mock.call(view_index, mock.ANY),
            m_venusian.attach.call_args_list[1]
            )

    def test_callback(self):
        pass




