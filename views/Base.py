from django.http import HttpRequest, HttpResponse
from CTUtil.Response.response import resp_error_json, resp_to_json
from typing import Dict, Union, List
from django.conf.urls import url


class BaseView(object):

    model_name = None
    route_name = None
    methods = ['delete', 'update', 'add', 'query']
    protect = True
    process_request = []

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def process_model_and_route(self):
        if not (self.model_name and self.route_name):
            raise ValueError('model_name or route_name is None')

    def process_request_post(
            self, request: HttpRequest) -> Dict[str, Union[str, int]]:
        return request.POST

    def query(self, request: HttpRequest) -> HttpResponse:
        return_data = {
            'state': 0,
            'data': list(self.model_name.objects.all()),
        }
        return resp_to_json(return_data)

    def delete(self, request: HttpRequest) -> HttpResponse:
        self.process_model_and_route()
        reqall: Dict[str, str] = request.POST
        _id: int = int(reqall.get('id', 0))
        if not _id:
            return resp_error_json('id不允许为空')
        query = self.model_name.objects.filter(id=_id)
        if not query:
            return resp_error_json('数据不存在')
        query.delete()
        return_data: Dict[str, Union[str, int]] = {
            'state': 0,
            'data': '删除成功',
        }
        return resp_to_json(return_data)

    def update(self, request: HttpRequest) -> HttpResponse:
        self.process_model_and_route()
        reqall: Dict[str, str] = self.process_request_post(request)
        _id: int = int(reqall.setdefault('id', 0))
        if not _id:
            return resp_to_json('id不允许为空')
        reqall.pop('id')
        query = self.model_name.objects.filter(id=_id)
        if not query:
            return resp_error_json('数据不存在')
        query.update(reqall)
        return_data: Dict[str, Union[str, int]] = {
            'state': 0,
            'data': '修改成功',
        }
        return resp_to_json(return_data)

    def add(self, request: HttpRequest) -> HttpResponse:
        self.process_model_and_route()
        reqall: Dict[str, Union[str, int]] = self.process_request_post(request)
        self.model_name.objects.create(**reqall)
        return_data: Dict[str, Union[str, int]] = {
            'state': 0,
            'data': '新增成功',
        }
        return resp_error_json(return_data)

    def default(self, request: HttpRequest) -> HttpResponse:
        return_data: Dict[str, Union[str, int]] = {
            'state': 1,
            'data': 'error url path',
        }
        resp: HttpResponse = resp_to_json(return_data)
        resp.status_code = 404
        return resp

    @classmethod
    def as_view(cls, _method, **init):
        def view(request: HttpRequest, *args, **kwargs):
            self = cls(**init)
            handle = getattr(self, _method, 'default')
            return handle(request, *args, **kwargs)
        return view

    @classmethod
    def as_urls(cls, django_url_list):
        _methods: List[str] = cls.methods if not cls.protect else ['add', 'query']
        for method_name in _methods:
            path = '{method_name}-{route_name}'.format(
                method_name=method_name,
                route_name=cls.route_name, )
            django_url_list.append(url(path, cls.as_view(method_name)))
