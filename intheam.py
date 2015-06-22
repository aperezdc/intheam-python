#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2015 Adrian Perez <aperez@igalia.com>
#
# Distributed under terms of the MIT license.

"""
Python module for accessing the inthe.am API.

The API consumed by this module is described here:
http://intheam.readthedocs.org/en/latest/api/index.html
"""
from datetime import datetime
import aiohttp
import json
import schema
import uuid


BASE_URL = "https://inthe.am/api/v1"


class Enum(object):
    def __init__(self, name, *arg, **kw):
        self.__name__ = name
        self.__reverse_map = {}

        for name in arg:
            name = str(name)
            kw[name] = name
        for k, v in kw.items():
            setattr(self, k, v)
            self.__reverse_map[v] = k

    def value(self, name):
        return getattr(self, name)

    def name(self, value):
        return self.__reverse_map[value]

    def __contains__(self, name):
        return hasattr(self, name)

    def __call__(self, value):
        if value in self.__reverse_map:
            return value
        elif isinstance(value, str) and value in self:
            return self.value(value)
        else:
            raise ValueError(value)


Priority = Enum("Priority", "H", "M", "L")
Status   = Enum("Status", "pending", "completed", "waiting", "deleted")

DATE_FORMAT = "%a, %d %b %Y %H:%M:%S %z"
def parse_date(s):
    from datetime import datetime
    if isinstance(s, datetime):
        return s
    return datetime.strptime(s, DATE_FORMAT)

def parse_uuid(s):
    if isinstance(s, uuid.UUID):
        return s
    return uuid.UUID(s)

SchemaUUID   = schema.Use(parse_uuid)
SchemaDate   = schema.Use(parse_date)
SchemaString = schema.And(str, len)


annotation_schema = schema.Schema({
    "description" : SchemaString,
    "entry"       : schema.Or(None, SchemaDate),
})


class Schemed(object):
    __schema__ = None
    __slots__  = ("_data",)

    def __init__(self, *arg, **kw):
        object.__setattr__(self, "_data", ())
        self.update(*arg, **kw)

    def __getattr__(self, key):
        d = object.__getattribute__(self, "_data")
        if key in d:
            return d[key]
        else:
            return object.__getattribute__(self, key)

    def __setattr__(self, key, value):
        if key.startswith("_"):
            object.__setattr__(self, key, value)
        else:
            self.update({ key: value })

    def update(self, *arg, **kw):
        d = dict(object.__getattribute__(self, "_data"))
        d.update(*arg, **kw)
        object.__setattr__(self, "_data", self.__schema__.validate(d))
        return self

    def to_json(self, *arg, **kw):
        d = dict(object.__getattribute__(self, "_data"))
        return CustomJSONEncoder(*arg, **kw).encode(d)

    def __iter__(self):
        return object.__getattribute__(self, "_data").items()

    def keys(self):
        return self._data.keys()

    @classmethod
    def validate(cls, data):
        if isinstance(data, cls):
            return data
        elif isinstance(data, dict):
            return cls(**data)
        else:
            raise ValueError(data)


class Annotation(Schemed):
    __schema__ = schema.Schema({
        "description" : SchemaString,
        "entry"       : schema.Or(None, SchemaDate),
    })
    __NOW = object()

    def __init__(self, description, entry=__NOW):
        if entry is self.__NOW:
            entry = datetime.now()
        super(Annotation, self).__init__(
                description=description,
                entry=entry)

    @classmethod
    def validate(cls, data):
        if isinstance(data, str):
            return cls(data, None)
        else:
            return super(Annotation, cls).validate(data)


class Task(Schemed):
    __schema__ = schema.Schema({
        "description"  : SchemaString,
        "status"       : schema.Or(None, schema.Use(Status)),
        "priority"     : schema.Or(None, schema.Use(Priority)),
        "id"           : SchemaUUID,
        "annotations"  : [Annotation],
        "blocks"       : [SchemaUUID],
        "depends"      : [SchemaUUID],
        "due"          : schema.Or(None, SchemaDate),
        "entry"        : SchemaDate,
        "modified"     : SchemaDate,
        "progress"     : schema.Or(None, float),
        "project"      : schema.Or(None, SchemaString),
        "scheduled"    : schema.Or(None, SchemaDate),
        "start"        : schema.Or(None, SchemaDate),
        "short_id"     : int,
        "urgency"      : float,
        "tags"         : [SchemaString],

        # Optional values added by the inthe.am API,
        # which locally created tasks do not have
        schema.Optional("resource_uri") : schema.Or(None, SchemaString),
        schema.Optional("url")          : schema.Or(None, SchemaString),
        schema.Optional("uuid")         : SchemaUUID,

        # Validated but ignored.
        "imask" : schema.Or(None, str),
        "wait"  : schema.Or(None, uuid.UUID),

        # inthe.am specific values; also validated but not used.
        # TODO: Check whether those are completely correct
        schema.Optional("intheamattachments")          : schema.Or(None, [SchemaString]),
        schema.Optional("intheamkanbanassignee")       : schema.Or(None, str),
        schema.Optional("intheamkanbanboarduuid")      : schema.Or(None, uuid.UUID),
        schema.Optional("intheamkanbancolor")          : schema.Or(None, str),
        schema.Optional("intheamkanbancolumn")         : schema.Or(None, str),
        schema.Optional("intheamkanbansortorder")      : schema.Or(None, str),
        schema.Optional("intheamkanbantaskuuid")       : schema.Or(None, uuid.UUID),
        schema.Optional("intheamoriginalemailid")      : schema.Or(None, str),
        schema.Optional("intheamoriginalemailsubject") : schema.Or(None, str),
    })

    def __init__(self, api=None, **kw):
        super(Task, self).__init__(**kw)
        self.__api = api

    def refresh_data(self):
        return self.__api.refresh_task(self)

    def mark_started(self):
        return self.__api.start_task(self)

    def mark_stopped(self):
        return self.__api.stop_task(self)

    def delete(self):
        return self.__api.delete_task(self)


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.strftime(DATE_FORMAT)
        elif isinstance(o, uuid.UUID):
            return str(o)
        elif isinstance(o, Schemed):
            return dict(iter(o))
        return super(JSONEncoder, self).default(o)


class InTheAmError(Exception):
    """Exception class uses for inthe.am API errors."""
    def __init__(self, response):
        error_line = self.ERROR_MAP.get(response.status,
                "Unspecified/unknown error")
        super(InTheAmError, self).__init__(
                "{!s}: {}\n{!s}".format(
                    response.status,
                    error_line,
                    response.text()))

class NotFound(InTheAmError):
    """Exception raised when a resource is not found."""

class NotAuthenticated(InTheAmError):
    """Exception raised on unauthorized/unauthenticated access a resource."""


class InTheAm(object):
    def __init__(self, auth_token, base_url=BASE_URL):
        self.auth_token = str(auth_token)
        self.base_url   = str(base_url)
        self._session   = aiohttp.ClientSession(headers={
                "Authorization": "ApiKey " + self.auth_token,
            })

    def __del__(self):
        self._session.close()

    def pending(self):
        response = yield from self._session.get(self.base_url + "/task/")
        body = yield from response.json()
        return (Task(api=self, **item) for item in body.get("objects", ()))

    def completed(self):
        response = yield from self._session.get(
                self.base_url + "/completedtask/")
        body = yield from response.json()
        return (Task(api=self, **item) for item in body.get("objects", ()))

    def user_status(self):
        response = yield from self._session.get(
                self.base_url + "/user/status/")
        return (yield from response.json())

    def __get_task_dict(self, task_uuid):
        response = yield from self._session.get(
                "{.base_url}/task/{!s}/".format(self, task_uuid))
        return (yield from response.json())

    def __check_response(self, response, json=False):
        if response.status in (200, 201):
            if json:
                return (yield from response.json())
            else:
                return (yield from response.text())
        elif response.status in (401, 403):
            raise NotAuthenticated(response)
        elif response.status == 404:
            raise NotFound(response)
        else:
            raise InTheAmError(response)

    def task(self, task_uuid):
        return Task(api=self, **(yield from self.__get_task_dict(task_uuid)))

    def refresh_task(self, task):
        return task.update(self.__get_task_dict(task.uuid))

    def save_task(self, task):
        response = yield from self._session.put(
                "{.base_url}/task/{.uuid!s}/".format(self, task),
                data=task.to_json())
        _ = yield from self.__check_response(response)
        return self.refresh_task(task)

    def start_task(self, task):
        response = yield from self._session.post(
                "{.base_url}/task/{.uuid!s}/".format(self, task))
        _ = yield from self.__check_response(response)
        return self.refresh_task(task)

    def stop_task(self, task):
        response = yield from self._session.post(
                "{.base_url}/task/{.uuid!s}/".format(self, task))
        _ = yield from self.__check_response(response)
        return self.refresh_task(task)

    def delete_task(self, task):
        response = yield from self._session.post(
                "{.base_url}/task/{.uuid!s}/delete/".format(self, task))
        _ = yield from self.__check_response(response)
        return self.refresh_task(task)

    def complete_task(self, task):
        response = yield from self._session.delete(
                "{.base_url}/task/{.uuid!s}/".format(self, task))
        _ = yield from self.__check_response(response)
        return self.refresh_task(task)
