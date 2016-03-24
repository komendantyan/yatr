#!/usr/bin/env python
# coding: utf-8

import requests


class YandexExeption(Exception):
    messages = {}

    def __init__(self, status_code):
        message = self.messages.get(status_code, 'Unknown exeption')
        if status_code is None:
            status_code = -1
        super(YandexExeption, self).__init__(
            "(%d) %s" % (status_code, message))


class YandexAPI(object):
    def __init__(self, key):
        self.key = key

    def _call_method(self, api_method, http_method='get', **kargs):
        if kargs.get('params') is not None:
            kargs['params']['key'] = self.key
        else:
            kargs['params'] = {'key': self.key}

        response = requests.request(
            http_method,
            self.url.format(method=api_method),
            **kargs
        )

        if not response.headers['Content-Type'].startswith('application/json'):
            raise self._exception(response.status_code)
        else:
            answer = response.json()
            if isinstance(answer, dict):
                code = answer.get('code', response.status_code)
            else:
                code = response.status_code
            if code != 200:
                raise self._exception(code)
            else:
                return answer


class YandexTranslatorException(YandexExeption):
    messages = {
        200: "Операция выполнена успешно",
        401: "Неправильный ключ API",
        402: "Ключ API заблокирован",
        403: "Превышено суточное ограничение на количество запросов",
        404: "Превышено суточное ограничение на объем переведенного текста",
        413: "Превышен максимально допустимый размер текста",
        422: "Текст не может быть переведен",
        501: "Заданное направление перевода не поддерживается",
    }


class YandexTranslatorAPI(YandexAPI):
    url = "https://translate.yandex.net/api/v1.5/tr.json/{method}"
    _exception = YandexTranslatorException

    def detect(self, text, hint=[]):
        answer = self._call_method(
            'detect',
            params={
                'text': text,
                'hint': ','.join(hint),
            }
        )
        return answer['lang']

    def get_langs(self, ui=None):
        if ui is None:
            params = None
        else:
            params = {'ui': ui}

        answer = self._call_method(
            'getLangs',
            params=params
        )
        if ui is None:
            return answer['dirs']
        else:
            return answer['langs']

    def translate(self, text, lang, format=None, options=None):
        params = {
            'text': text,
            'lang': lang
        }
        if format is not None:
            params['format'] = format
        if options is not None:
            params['options'] = options

        answer = self._call_method(
            'translate',
            params=params
        )
        return answer


class YandexDictionaryException(YandexExeption):
    messages = {
        401: "Ключ API невалиден.",
        402: "Ключ API заблокирован.",
        403: "Превышено суточное ограничение на количество запросов.",
        413: "Превышен максимальный размер текста.",
        501: "Заданное направление перевода не поддерживается.",
    }


class YandexDictionaryAPI(YandexAPI):
    url = "https://dictionary.yandex.net/api/v1/dicservice.json/{method}"
    _exception = YandexDictionaryException

    def get_langs(self):
        answer = self._call_method(
            'getLangs',
        )
        return answer

    def lookup(self, text, lang, ui='ru', flags=None):
        params = {
            'text': text,
            'lang': lang,
            'ui': ui,
        }
        if flags is not None:
            params['flags'] = flags

        answer = self._call_method(
            'lookup',
            params=params
        )
        return answer['def']
