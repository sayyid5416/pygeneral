"""
Module for signal and slot related functions
"""
from logging import Logger
import logging
from typing import Any, Callable

"""
Items imported inside functions/classes

- from .decorator import run_threaded
- from .general import generate_repr_str
"""



class Signal:
    """
    A signal object that can be used to connect callback.
    - Connect a callback using `.connect(...)` method
        - Newer callback will overwrite the older callback
    - Emit the signal using `.emit(...)` method to run the connected callback
    
    Args:
        - `name`: Name of the signal
        - `threaded`: Emit the signal in a new thread (can be overridden during `.emit(...)`)
        - `daemon`: If `threaded`, thread should be daemon or not
        - `logger`: `Logger` to be used for logging
    """

    def __init__(
        self, name = 'Signal',
        threaded = False,
        daemon = False,
        logger: Logger | None = None
    ):
        # Mods
        if logger is None:
            from ._utils import _get_basic_logger
            logger = _get_basic_logger()

        # Args
        self.name = name
        self.threaded = threaded
        self.daemon = daemon
        self.logger = logger

        # Data
        self._callback: Callable | None = None
        self.cb_args = tuple()
        self.cb_kwargs = dict()
        self._set_default_values()
    
    def __repr__(self) -> str:
        from .general import generate_repr_str
        return generate_repr_str(
            self, 'name', 'threaded', 'daemon', 'logger'
        )
    
    def _set_default_values(self):
        """ Sets the default values for items """
        self._callback = None
        self.cb_args = tuple()
        self.cb_kwargs = dict()

    def connect(self, callback: Callable, *args, **kwargs):
        """ Connect `callback` to signal """
        self._callback = callback
        self.cb_args = args
        self.cb_kwargs = kwargs
        self.logger.debug(f'Callback "{callback.__name__}({args=}, {kwargs=})" setted for "{self.name}" signal')

    def disconnect(self, callback: Callable, ignoreError = False):
        """ 
        Disconnect `callback` from signal
        - raise `ValueError`, if `callback` is not connected to signal
        - If `ignoreError = True`, `ValueError` won't be raised
        """
        if self._callback != callback:
            if ignoreError:
                self.logger.debug(f'"{callback.__name__}" is not connected to "{self.name}" signal')
                return
            raise ValueError(f'"{callback.__name__}" is not connected to "{self.name}" signal')
        self.logger.debug(f'Removed "{callback.__name__}" from "{self.name}" signal')
        self._set_default_values()

    def emit(self, threaded: bool | None = None, *args: Any, **kwargs: Any):
        """
        Emit the signal with the given arguments
        - Connected callback will run with `args` and `kwargs` (if present)
            - These `args` and `kwargs` be passed along with those which were set in `.connect(...)` method
            - These `kwargs` will take precedence (in case of duplication) over those which were set in `.connect(...)` method
            - Final Args would be like `(earlier_args, these_args, final_kwargs)`
        - `threaded`: If `True/False`, It overrides the behavior of `threaded` setted during `Signal(threaded=..., ...)`
        """
        # Modify
        _threaded = self.threaded if threaded is None else threaded
        _args = self.cb_args + args
        _kwargs = {**self.cb_kwargs, **kwargs}

        # Run
        if self._callback:
            if _threaded:
                from .decorator import run_threaded
                run_threaded(
                    daemon=self.daemon,
                    name=f'Signal Thread {self._callback.__name__}',
                    logger=self.logger,
                )(self._callback)(*_args, **_kwargs)
            else:
                self._callback(*_args, **_kwargs)

