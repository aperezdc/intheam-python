#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2015-2016 Adrian Perez <aperez@igalia.com>
#
# Distributed under terms of the MIT license.

import gnarl
import intheam
import unittest


class TestAnnotation(unittest.TestCase):
    def test_create_description_only(self):
        ann = intheam.Annotation("Foo bar")
        self.assertIsInstance(ann, intheam.Annotation)
        self.assertEqual("Foo bar", ann.description)
        # A default value for the "entry" date must have been created
        self.assertIsInstance(ann.entry, gnarl.Timestamp)

    def test_create_datetime(self):
        now = intheam.SchemaDate.now()
        ann = intheam.Annotation("Foo bar", now)
        self.assertIsInstance(ann, intheam.Annotation)
        self.assertEqual("Foo bar", ann.description)
        self.assertIsInstance(ann.entry, intheam.SchemaDate)
        self.assertEqual(ann.entry, now)

    def test_create_string_date(self):
        ann = intheam.Annotation("Foo bar", "Mon, 22 Jun 2015 23:13:31 +0100")
        self.assertIsInstance(ann, intheam.Annotation)
        # Conversion should have happened automatically
        self.assertIsInstance(ann.entry, intheam.SchemaDate)

    def test_create_no_date(self):
        ann = intheam.Annotation("Foo bar", None)
        self.assertIsInstance(ann, intheam.Annotation)
        self.assertIs(ann.entry, None)

    def test_create_from_dict(self):
        data = {
            "description" : "Foo bar",
            "entry" : "Mon, 22 Jun 2015 22:46:00 +0100",
        }
        ann = intheam.Annotation.validate(data)
        self.assertIsInstance(ann, intheam.Annotation)
        self.assertIsInstance(ann.entry, gnarl.Timestamp)
        from delorean.interface import parse
        self.assertEqual(ann.entry, parse(data["entry"]))

    def test_create_from_dict_datetime(self):
        data = {
            "description" : "Foo bar",
            "entry" : intheam.SchemaDate.validate("Mon, 22 Jun 2015 22:46:00 +0100"),
        }
        ann = intheam.Annotation.validate(data)
        self.assertIsInstance(ann, intheam.Annotation)
        self.assertIsInstance(ann.entry, gnarl.Timestamp)

    def test_create_from_dict_no_date(self):
        ann = intheam.Annotation.validate({
            "description" : "Foo bar", "entry" : None})
        self.assertIsInstance(ann, intheam.Annotation)
        self.assertIs(ann.entry, None)

    def test_to_json(self):
        ann = intheam.Annotation("Foo bar", "Mon, 22 Jun 2015 00:00:00 +0000")
        json = ann.to_json(sort_keys=True)
        self.assertEqual(json,
            '{"description": "Foo bar", "entry": "Mon, 22 Jun 2015 00:00:00 +0000"}')

    def test_data_keys(self):
        ann = intheam.Annotation("Foo bar")
        self.assertEqual(list(sorted(ann.keys())), ["description", "entry"])

    def test_validate_instance(self):
        ann = intheam.Annotation("Foo bar")
        r = intheam.Annotation.validate(ann)
        self.assertIs(r, ann)

    def test_validate_string(self):
        ann = intheam.Annotation.validate("Foo bar")
        self.assertIsInstance(ann, intheam.Annotation)
        self.assertIs(ann.entry, None)
        self.assertEqual(ann.description, "Foo bar")
