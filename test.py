#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2015 Adrian Perez <aperez@igalia.com>
#
# Distributed under terms of the MIT license.

import intheam
import unittest

continents = ("EUROPE", "AFRICA", "OCEANIA", "AMERICA", "ANTARCTICA", "ASIA")


class TestEnum(unittest.TestCase):
    def test_stringvalues(self):
        Continent = intheam.Enum("Continent", *continents)
        self.assertIsInstance(Continent, intheam.Enum)
        self.assertEquals("Continent", Continent.__name__)
        for continent in continents:
            self.assertEquals(continent, getattr(Continent, continent))

    def test_intvalues(self):
        Continent = intheam.Enum("Continent", **dict(
            ((continents[i], i) for i in range(len(continents)))
        ))
        for i in range(len(continents)):
            self.assertEqual(i, getattr(Continent, continents[i]))

    def test_object_value(self):
        unique_value = object()
        E = intheam.Enum("E", Unique=unique_value)
        self.assertIs(unique_value, E.Unique)
        self.assertIs(unique_value, E.value("Unique"))
        self.assertIs("Unique", E.name(unique_value))
        self.assertIs(unique_value, E(unique_value))
        self.assertIs(unique_value, E("Unique"))

    def test_coercion(self):
        Continent = intheam.Enum("Continent", **dict(
            ((continents[i], i) for i in range(len(continents)))
        ))
        self.assertEquals(2, Continent.OCEANIA)
        self.assertEquals(2, Continent(2))
        self.assertEquals(2, Continent(Continent.OCEANIA))
        self.assertEquals(2, Continent("OCEANIA"))
        with self.assertRaises(ValueError):
            v = Continent("MARACAIBO")
        with self.assertRaises(ValueError):
            v = Continent(20)


class TestDateParsing(unittest.TestCase):
    valid = (
        "Mon, 22 Jun 2015 22:26:00 +0100",
        "Thu, 11 May 2983 19:35:45 -0230",
    )

    invalid = (
        "",
        "Blargh",
        # XXX: This is invalid because the date does not fall on Tuesday.
        #      In most systems strptime() does not check the given week day.
        # "Tue, 22 Jun 2015 22:26:00 +0100",
        "22 Jun 2015",
        "00:45",
        "12:32:23",
        "Mon 22 Jun 2015 22:26:00 +0100",
        "Mon, 22 Jun 2015 45:90:00 +0100",
    )

    def test_parse_valid_dates(self):
        from datetime import datetime
        for date in self.valid:
            d = intheam.parse_date(date)
            self.assertIsInstance(d, datetime)

    def test_parse_invalid_dates(self):
        for date in self.invalid:
            with self.assertRaises(ValueError):
                d = intheam.parse_date(date)

    def test_parse_datetime_object(self):
        from datetime import datetime
        d = datetime.now()
        r = intheam.parse_date(d)
        self.assertIsInstance(r, datetime)
        self.assertIs(r, d)


class TestUUIDParsing(unittest.TestCase):
    valid = (
        "5c2ddc84-bf99-47d2-a0da-3882b9d788ed",
        "5C2DDC84-BF99-47D2-A0DA-3882B9D788ED",
        "5c2ddc84bf9947d2a0da3882b9d788ed",
        "5C2DDC84BF9947D2A0DA3882B9D788ED",
    )
    invalid = (
        "",
        "blargh",
        "AFCEDEFSDSDS",
    )

    def test_parse_valid_uuids(self):
        from uuid import UUID
        for u in self.valid:
            uuid = intheam.parse_uuid(u)
            self.assertIsInstance(uuid, UUID)

    def test_parse_invalid_uuids(self):
        for u in self.invalid:
            with self.assertRaises(ValueError):
                r = intheam.parse_uuid(u)

    def test_parse_uuid_object(self):
        from uuid import UUID, uuid1
        u = uuid1()
        r = intheam.parse_uuid(u)
        self.assertIsInstance(r, UUID)
        self.assertIs(r, u)


class TestAnnotation(unittest.TestCase):
    def test_create_description_only(self):
        ann = intheam.Annotation("Foo bar")
        self.assertIsInstance(ann, intheam.Annotation)
        self.assertEqual("Foo bar", ann.description)
        # A default value for the "entry" date must have been created
        from datetime import datetime
        self.assertIsInstance(ann.entry, datetime)

    def test_create_datetime(self):
        from datetime import datetime
        now = datetime.now()
        ann = intheam.Annotation("Foo bar", now)
        self.assertIsInstance(ann, intheam.Annotation)
        self.assertEqual("Foo bar", ann.description)
        self.assertIsInstance(ann.entry, datetime)
        self.assertIs(ann.entry, now)

    def test_create_string_date(self):
        ann = intheam.Annotation("Foo bar", "Mon, 22 Jun 2015 23:13:31 +0100")
        self.assertIsInstance(ann, intheam.Annotation)
        # Conversion should have happened automatically
        from datetime import datetime
        self.assertIsInstance(ann.entry, datetime)

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
        from datetime import datetime
        self.assertIsInstance(ann.entry, datetime)
        self.assertEqual(ann.entry, intheam.parse_date(data["entry"]))

    def test_create_from_dict_datetime(self):
        data = {
            "description" : "Foo bar",
            "entry" : intheam.parse_date("Mon, 22 Jun 2015 22:46:00 +0100"),
        }
        ann = intheam.Annotation.validate(data)
        self.assertIsInstance(ann, intheam.Annotation)
        from datetime import datetime
        self.assertIsInstance(ann.entry, datetime)

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
