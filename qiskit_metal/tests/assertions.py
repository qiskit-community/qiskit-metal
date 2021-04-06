# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

# pylint: disable-msg=unnecessary-pass
# pylint: disable-msg=invalid-name
# pylint: disable-msg=bad-continuation
"""Custom assertion for unit tests."""

from itertools import zip_longest
from typing import Iterable, Optional


class AssertionsMixin:
    """Custom assertions for unit tests."""

    def assertAlmostEqualRel(
        self,
        expected: float,
        tested: float,
        *,
        msg: Optional[str] = None,
        rel_tol: float = 1e-7,
        abs_tol: float = 0.0,
    ):
        """Assert tested almost equals expected.

        Args:
            expected (float): Expected value to compare to.
            tested (float): Value to compare to expected.
            msg (Optional[str]): Custom message to show on failure.  Defaults to None.
            rel_tol (float): Relative tolerance to accept.  Defaults to 1e-7.
            abs_tol (float): Absolute tolerance to accept.  Defaults to 0.0.

        Return:
            Exception: Failure exception, or nothing
        """
        if expected == tested:
            return

        rel_diff = abs((expected - tested) / expected)
        abs_diff = abs(expected - tested)

        if rel_diff <= rel_tol or abs_diff <= abs_tol:
            return

        if rel_diff > rel_tol:
            standardMsg = (
                f"Relative difference {rel_diff} exceeds tolerance {rel_tol} "
                f"for expected={expected}, tested={tested}")
            msg = self._formatMessage(msg, standardMsg)
            raise self.failureException(msg)

        if abs_diff > abs_tol:
            standardMsg = (
                f"Absolute difference {abs_diff} exceeds tolerance {abs_tol} "
                f"for expected={expected}, tested={tested}")
            msg = self._formatMessage(msg, standardMsg)
            raise self.failureException(msg)

    def assertIterableAlmostEqual(
        self,
        expected: Iterable[float],
        tested: Iterable[float],
        msg: Optional[str] = None,
        rel_tol: float = 1e-7,
        abs_tol: float = 0.0,
    ):
        """Assert all entries in two iterables are almost equal.

        Args:
            expected (Iterable[float]): First iterable to compare.
            tested (Iterable[float]): Second iterable to compare.
            msg (Optional[str]): Custom message to show for failure.  Defaults to None.
            rel_tol (float): Relative tolerance to accept.  Defaults to 1e-7.
            abs_tol (float): Absolute tolerance to accept.  Defaults to 0.0.

        Return:
            Exception: Failure exception, or nothing
        """
        sentinel = object()
        for index, (item1, item2) in enumerate(
                zip_longest(expected, tested, fillvalue=sentinel)):
            if sentinel in (item1, item2):
                standardMsg = (
                    f"Iterables have unequal lengths. One has {index} and the "
                    "other has more.")
                msg = self._formatMessage(msg, standardMsg)
                raise self.failureException(msg)

            try:
                self.assertAlmostEqualRel(item1,
                                          item2,
                                          rel_tol=rel_tol,
                                          abs_tol=abs_tol)
            except AssertionError as err:
                standardMsg = f"Iterable elements {index} not almost equal: {str(err)}"
                msg = self._formatMessage(msg, standardMsg)
                raise self.failureException(msg) from None
