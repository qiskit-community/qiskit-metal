from functools import wraps
from .. import logger
import inspect
import traceback
import types


class ComponentInitFailedError(Exception):

    def __init__(self, msg=None, *args, **kwargs):
        super().__init__(msg, *args, **kwargs)
