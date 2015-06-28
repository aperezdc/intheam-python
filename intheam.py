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

import lasso
import aiohttp
import schema
import uuid


BASE_URL = "https://inthe.am/api/v1"


class Priority(lasso.Enum):
    HIGH   = "H"
    MEDIUM = "M"
    LOW    = "L"

class Status(lasso.Enum):
    PENDING   = "pending"
    COMPLETED = "completed"
    WAITING   = "waiting"
    DELETED   = "deleted"


class SchemaDate(lasso.Timestamp):
    __format__ = lasso.Timestamp.FORMAT_RFC_2822

SchemaString = lasso.And(str, len)


class Annotation(lasso.Schemed):
    __schema__ = {
        "description" : SchemaString,
        "entry"       : lasso.Or(None, SchemaDate),
    }
    __NOW = object()

    def __init__(self, description, entry=__NOW):
        if entry is self.__NOW:
            entry = SchemaDate.now()
        super(Annotation, self).__init__(
                description=description,
                entry=entry)

    @classmethod
    def validate(cls, data):
        if isinstance(data, str):
            return cls(data, None)
        else:
            return super(Annotation, cls).validate(data)


class Task(lasso.Schemed):
    __schema__ = {
        "description"  : SchemaString,
        "status"       : lasso.Or(None, Status),
        "priority"     : lasso.Or(None, Priority),
        "id"           : lasso.UUID,
        "annotations"  : [Annotation],
        "blocks"       : [lasso.UUID],
        "depends"      : [lasso.UUID],
        "due"          : lasso.Or(None, SchemaDate),
        "entry"        : SchemaDate,
        "modified"     : SchemaDate,
        "progress"     : lasso.Or(None, float),
        "project"      : lasso.Or(None, SchemaString),
        "scheduled"    : lasso.Or(None, SchemaDate),
        "start"        : lasso.Or(None, SchemaDate),
        "short_id"     : int,
        "urgency"      : float,
        "tags"         : [SchemaString],

        # Optional values added by the inthe.am API,
        # which locally created tasks do not have
        lasso.Optional("resource_uri") : lasso.Or(None, SchemaString),
        lasso.Optional("url")          : lasso.Or(None, SchemaString),
        lasso.Optional("uuid")         : lasso.UUID,

        # Validated but ignored.
        "imask" : lasso.Or(None, str),
        "wait"  : lasso.Or(None, lasso.UUID),

        # inthe.am specific values; also validated but not used.
        # TODO: Check whether those are completely correct
        lasso.Optional("intheamattachments")          : schema.Or(None, [SchemaString]),
        lasso.Optional("intheamkanbanassignee")       : schema.Or(None, str),
        lasso.Optional("intheamkanbanboarduuid")      : schema.Or(None, lasso.UUID),
        lasso.Optional("intheamkanbancolor")          : schema.Or(None, str),
        lasso.Optional("intheamkanbancolumn")         : schema.Or(None, str),
        lasso.Optional("intheamkanbansortorder")      : schema.Or(None, str),
        lasso.Optional("intheamkanbantaskuuid")       : schema.Or(None, lasso.UUID),
        lasso.Optional("intheamoriginalemailid")      : schema.Or(None, str),
        lasso.Optional("intheamoriginalemailsubject") : schema.Or(None, str),
    }

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
