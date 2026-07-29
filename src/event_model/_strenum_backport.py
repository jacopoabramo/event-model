# StrEnum is vendored from backports.strenum 1.3.1
# https://github.com/clbarnes/backports.strenum
#
# The package is verbatim copy of CPython 3.11's enum.StrEnum.
#
# Remove when supporting Python 3.10 is dropped.
#
# Copyright (c) 2001-2023 Python Software Foundation; All Rights Reserved
#
# Licensed under the Python Software Foundation License Version 2.
"""Vendored backport of StrEnum from Python 3.11."""

from enum import Enum
from typing import TypeVar

_S = TypeVar("_S", bound="StrEnum")


class StrEnum(str, Enum):
    def __new__(cls: type[_S], *values: str) -> _S:
        if len(values) > 3:
            raise TypeError(f"too many arguments for str(): {values}")
        if len(values) == 1:
            # it must be a string
            if not isinstance(values[0], str):
                raise TypeError(f"{values[0]!r} is not a string")
        if len(values) >= 2:
            # check that encoding argument is a string
            if not isinstance(values[1], str):
                raise TypeError(f"encoding must be a string, not {values[1]!r}")
        if len(values) == 3:
            # check that errors argument is a string
            if not isinstance(values[2], str):
                raise TypeError(f"errors must be a string, not {values[2]!r}")
        value = str(*values)
        member = str.__new__(cls, value)
        member._value_ = value
        return member

    __str__ = str.__str__

    @staticmethod
    def _generate_next_value_(
        name: str, start: int, count: int, last_values: list[str]
    ) -> str:
        return name.lower()


__all__ = ["StrEnum"]
