# Copyright 2017 The Nuclio Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import datetime
import io

import nuclio_sdk.test
import nuclio_sdk.helpers


class TestLogger(nuclio_sdk.test.TestCase):
    def setUp(self):
        self._io = io.StringIO()
        self._logger = nuclio_sdk.Logger(logging.DEBUG, "test_logger")
        self._logger.set_handler("default", self._io, nuclio_sdk.logger.JSONFormatter())

    def test_log_text(self):
        """
        message only log line is printed
        """

        self._logger.debug("TestA")
        self.assertIn("TestA", self._io.getvalue())

    def test_log_with_char(self):
        """
        log line with text kwarg
        """

        self._logger.debug_with("TestB", char="a")
        self.assertIn("TestB", self._io.getvalue())
        self.assertIn('"with": {"char": "a"}', self._io.getvalue())

    def test_log_with_number(self):
        """
        log line with int kwarg
        """

        self._logger.debug_with("TestC", number=1)
        self.assertIn("TestC", self._io.getvalue())
        self.assertIn('"with": {"number": 1}', self._io.getvalue())

    def test_log_with_date(self):
        """
        log line with datetime kwarg
        """

        date = datetime.datetime.strptime("Oct 1 2020", "%b %d %Y")
        self._logger.debug_with("TestD", date=date)
        self.assertIn("TestD", self._io.getvalue())
        self.assertIn(
            '"with": {"date": "datetime.datetime(2020, 10, 1, 0, 0)"}',
            self._io.getvalue(),
        )

    def test_log_nan(self):
        self._logger.info_with(self._testMethodName, nan=float("NaN"))
        self.assertIn(self._testMethodName, self._io.getvalue())
        self.assertIn(
            '"with": {"nan": "NaN"}',
            self._io.getvalue(),
        )

    def test_log_infinity(self):
        self._logger.info_with(self._testMethodName, nan=float("Infinity"))
        self.assertIn(self._testMethodName, self._io.getvalue())
        self.assertIn(
            '"with": {"nan": "Infinity"}',
            self._io.getvalue(),
        )

    def test_log_minus_infinity(self):
        self._logger.info_with(self._testMethodName, nan=float("-Infinity"))
        self.assertIn(self._testMethodName, self._io.getvalue())
        self.assertIn(
            '"with": {"nan": "-Infinity"}',
            self._io.getvalue(),
        )

    def test_fail_to_log(self):
        """
        Do not fail logging when an object is not log-able
        """

        class SomeObject(object):
            def __str__(self):
                raise Exception("I am not a string")

            def __repr__(self):
                raise Exception("Not yet a repr")

            def __log__(self):
                raise Exception("All I need is time")

        self._logger.debug_with("TestD", some_instance=SomeObject())
        self.assertIn("TestD", self._io.getvalue())
        self.assertIn(
            '"with": {"some_instance": "Unable to serialize object: I am not a string"}',
            self._io.getvalue(),
        )

    def test_redundant_logger_creation(self):

        # create 3 loggers with the same name
        logger1 = nuclio_sdk.Logger(logging.DEBUG, "test-logger")
        logger1.set_handler("default", self._io, nuclio_sdk.logger.JSONFormatter())
        logger2 = nuclio_sdk.Logger(logging.DEBUG, "test-logger")
        logger2.set_handler("default", self._io, nuclio_sdk.logger.JSONFormatter())
        logger3 = nuclio_sdk.Logger(logging.DEBUG, "test-logger")
        logger3.set_handler("default", self._io, nuclio_sdk.logger.JSONFormatter())

        # log from each logger and make sure only one log line is printed
        logger1.info("1")
        assert self._io.getvalue().count('"level": "info", "message": "1"') == 1
        logger2.info("2")
        assert self._io.getvalue().count('"level": "info", "message": "2"') == 1
        logger3.info("3")
        assert self._io.getvalue().count('"level": "info", "message": "3"') == 1
