# -*- coding: utf-8 -*-
from typing import Generic, TypeVar

from yaad import AttrDict  # type: ignore


def test_attr_dict():
    d = AttrDict(a=1, b=2)
    assert list(d.items()) == [("a", 1), ("b", 2)]

    assert d.a == 1

    d.c = 3
    assert d.c == 3
    assert list(d.items()) == [("a", 1), ("b", 2), ("c", 3)]

    del d["c"]
    assert list(d.items()) == [("a", 1), ("b", 2)]

    assert len(d) == 2

    del d.b

    assert len(d) == 1
    assert list(d.items()) == [("a", 1)]

    assert d._parent_key is None  # noqa: pylint: disable=protected-access
    del d._parent_key
    assert not hasattr(d, "_parent_key")


def test_nested_dict():
    d = AttrDict({"a": 1, "b": {"c": 2}})
    assert d.b.c == 2
    assert list(d.items()) == [("a", 1), ("b", AttrDict({"c": 2}))]
    assert list(d.items_flat()) == [("a", 1), ("b.c", 2)]

    assert str(d) == "AttrDict({'a': 1, 'b': {'c': 2}})"


def test_subclass():
    class SubAttrDict(AttrDict):
        def __init__(self, *args, account_id=None, **kwargs):
            super().__init__(*args, **kwargs)
            self.account_id = account_id

        def __class__init__(self, *args, **kwargs):
            return self.__class__(*args, account_id=self.account_id, **kwargs)

        _special_attributes = ("special_attr",)

        @property
        def special_attr(self):
            return "this is a special attribute"

    d = SubAttrDict({"a": 1, "b": {"c": 2}}, account_id=12354)
    assert list(d.items()) == [
        ("a", 1),
        ("b", SubAttrDict({"c": 2}, account_id=12354)),
        ("account_id", 12354),
        ("special_attr", "this is a special attribute"),
    ]


def test_wrapper():
    # noinspection PyPep8Naming
    T = TypeVar("T")

    class ROWrapper(Generic[T]):
        def __init__(self, data: T):
            self._data = data
            # self.__setattr__ = self.__sa__  # type: ignore

        def __getattr__(self, item):
            return getattr(self.data, item)

        def __getitem__(self, item):
            return self.data.__getitem__(item)

        def __setitem__(self, key, value):
            raise PermissionError("Cannot set item")

        def __delitem__(self, key):
            raise PermissionError("Cannot delete item")

        def __setattr__(self, key, value):  # noqa: pylint: disable=no-self-use
            if key == "_data":
                super().__setattr__(key, value)
            else:
                raise PermissionError("Cannot set attribute")

        def __delattr__(self, item):
            raise PermissionError("Cannot delete attribute")

    d = AttrDict({"a": 1, "b": {"c": 2}}, wrapper_type=ROWrapper)

    assert isinstance(d.a, ROWrapper)
    assert d.a._data == 1  # pylint: disable=protected-access

    i = list(d.items())
    assert i[0][1]._data == 1  # pylint: disable=protected-access
    assert isinstance(i[0][1], ROWrapper)
    i = list(d.items_flat())
    assert i[0][1]._data == 1  # pylint: disable=protected-access
    assert isinstance(i[0][1], ROWrapper)
