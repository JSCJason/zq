# -*- coding:utf-8 -*-
"""
@Time : 2021/5/8 23:06
@Author : domionlu@zquant.io
@File : restclient
"""
import traceback

# -*- coding:utf-8 -*-
from requests import Request, Session
from zq.common.tools import *
import zq.common.const as c
from loguru import logger as log


class RestClient:
    host = {}
    api = {}
    def __init__(self):
        self.lastRestRequestTimestamp = 0
        self.rateLimit = 2000
        self.enableRateLimit = False
        self.market_type = c.SPOT
        self.session = self.get_session()

    def get_session(self):
        return Session()

    def fetch(self, action, p=None):
        # 根据请求接口名称与数据，构造request
        request = self.build_request(action, data=p)
        data,rst = self.request(request)
        if rst:
        # 请求接口对应的解析函数，对返回数据进行格式转换
            fun ="parse_"+action.lower()
            if hasattr(self, fun):
                f = getattr(self, fun)
                return f(data)
            else:
                return data
        else:
            return data

    def get_api(self):
        return self.api.get(self.market_type)

    def get_url(self):
        return self.host.get(self.market_type)

    def build_request(self, action, **kwargs):
        """
        12.2 增加broker_type参数，根据所需要的交易类型，选择对应的api参数
        """
        api=self.get_api()
        api=api.get(action,None)
        host=self.get_url()
        if api:
            path = api.get("path")
            m = api.get("method")
            auth = api.get("auth")
            sign=api.get("SIGN",True)
            params = kwargs.get("data", None)
            request_path = path
            if m=="GET":
                request = Request(m, host + request_path, params=params)
            else:
                request = Request(m, host + request_path, data=params)
            # 是否为私有数据，进行签名处理
            if auth:
                request=self.sign_request(request,sign)
            return request
        else:
            return False

    def request(self, request):
        # 对接口访问是否有频率限制
        try:
            if self.enableRateLimit:
                self.delay()
            req=request.prepare()
            response = self.session.send(req)
            self.lastRestRequestTimestamp = get_cur_timestamp_ms()
            # 对返回结果进行简单处理
            return self._handel_request(response)
        except Exception as e:
            log.error(f"request error,{req}")

    def delay(self):
        now = get_cur_timestamp_ms()
        elapsed = now - self.lastRestRequestTimestamp
        if elapsed < self.rateLimit:
            d = self.rateLimit - elapsed
            time.sleep(d / 1000.0)

    def _handel_request(self, response):
        code = response.status_code
        if code not in (200, 201, 202, 203, 204, 205, 206, 400):
            text = response.text
            return text,False
        try:
            return response.json(),True
        except:
            return response.text,False

    def sign_request(self, request,sign=True):
        return request



