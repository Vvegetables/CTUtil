from django.http import HttpRequest, HttpResponse
from CTUtil.Response.response import resp_error_json, resp_to_json
from typing import Dict, Union, Type
from django.conf.urls import url
from enum import Enum, auto
from CTUtil.types import ResponseStates
from functools import wraps


class LoginMixin(object):
    def dispatch(self, _method, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return resp_error_json('用户未登录', ResponseStates.LOGIN_ERROR)
        return super(LoginMixin, self).dispatch(_method, request, *args,
                                                **kwargs)

    @classmethod
    def login_require(view_func):
        @wraps(view_func)
        def _process_request(request: Type[HttpRequest]):
            if request.user.is_authenticated:
                return resp_error_json('用户未登录', ResponseStates.LOGIN_ERROR)
            return view_func(request)

        return _process_request


class ControlMethods(Enum):
    delete = auto()
    add = auto()
    update = auto()
    query = auto()

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.__str__()


class BaseView(object):

    model_name = None
    route_name = None
    methods = ['delete', 'update', 'add', 'query']

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def process_model_and_route(self):
        if not (self.model_name and self.route_name):
            raise ValueError('model_name or route_name is None')

    def process_request_post(
            self, request: HttpRequest) -> Dict[str, Union[str, int]]:
        return request.POST.copy()

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
    def as_view(cls, _method: Type[ControlMethods], **init):
        def view(request: HttpRequest, *args, **kwargs):
            self = cls(**init)
            return self.dispatch(_method, request, *args, **kwargs)
        return view

    def dispatch(self, _method: Type[ControlMethods], request, *args, **kwargs):
        handle = getattr(self, _method.name, 'default')
        return handle(request, *args, **kwargs)

    @classmethod
    def as_urls(cls, django_url_list):
        for control_method in ControlMethods:
            path = '{method_name}-{route_name}'.format(
                method_name=control_method,
                route_name=cls.route_name, )
            django_url_list.append(url(path, cls.as_view(control_method)))
