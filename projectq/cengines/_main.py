# -*- coding: utf-8 -*-
#   Copyright 2017 ProjectQ-Framework (www.projectq.ch)
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
"""
Contains the main engine of every compiler engine pipeline, called MainEngine.
"""

import atexit
import sys
import traceback
import weakref

from projectq.ops import Command, FlushGate
from projectq.types import WeakQubitRef
from projectq.backends import Simulator

from ._basics import BasicEngine
from ._basicmapper import BasicMapperEngine


class NotYetMeasuredError(Exception):
    """Exception raised when trying to access the measurement value of a qubit that has not yet been measured."""


class UnsupportedEngineError(Exception):
    """Exception raised when a non-supported compiler engine is encountered"""


class _ErrorEngine:  # pylint: disable=too-few-public-methods
    """
    Fake compiler engine class only used to ensure gracious failure when an exception occurs in the MainEngine
    constructor.
    """

    def receive(self, command_list):  # pylint: disable=unused-argument
        """No-op"""


class MainEngine(BasicEngine):  # pylint: disable=too-many-instance-attributes
    """
    The MainEngine class provides all functionality of the main compiler engine.

    It initializes all further compiler engines (calls, e.g., .next_engine=...) and keeps track of measurement results
    and active qubits (and their IDs).

    Attributes:
        next_engine (BasicEngine): Next compiler engine (or the back-end).
        main_engine (MainEngine): Self.
        active_qubits (WeakSet): WeakSet containing all active qubits
        dirty_qubits (Set): Containing all dirty qubit ids
        backend (BasicEngine): Access the back-end.
        mapper (BasicMapperEngine): Access to the mapper if there is one.

    """

    def __init__(self, backend=None, engine_list=None, verbose=False):
        """
        Initialize the main compiler engine and all compiler engines.

        Sets 'next_engine'- and 'main_engine'-attributes of all compiler engines and adds the back-end as the last
        engine.

        Args:
            backend (BasicEngine): Backend to send the compiled circuit to.
            engine_list (list<BasicEngine>): List of engines / backends to use as compiler engines. Note: The engine
                list must not contain multiple mappers (instances of BasicMapperEngine).
                Default: projectq.setups.default.get_engine_list()
            verbose (bool): Either print full or compact error messages.
                            Default: False (i.e. compact error messages).

        Example:
            .. code-block:: python

                from projectq import MainEngine
                eng = MainEngine() # uses default engine_list and the Simulator

        Instead of the default `engine_list` one can use, e.g., one of the IBM
        setups which defines a custom `engine_list` useful for one of the IBM
        chips

        Example:
            .. code-block:: python

                import projectq.setups.ibm as ibm_setup
                from projectq import MainEngine
                eng = MainEngine(engine_list=ibm_setup.get_engine_list())
                # eng uses the default Simulator backend

        Alternatively, one can specify all compiler engines explicitly, e.g.,

        Example:
            .. code-block:: python

                from projectq.cengines import (TagRemover, AutoReplacer,
                                               LocalOptimizer,
                                               DecompositionRuleSet)
                from projectq.backends import Simulator
                from projectq import MainEngine
                rule_set = DecompositionRuleSet()
                engines = [AutoReplacer(rule_set), TagRemover(),
                           LocalOptimizer(3)]
                eng = MainEngine(Simulator(), engines)
        """
        super().__init__()
        self.active_qubits = weakref.WeakSet()
        self._measurements = dict()
        self.dirty_qubits = set()
        self.verbose = verbose
        self.main_engine = self

        if backend is None:
            backend = Simulator()
        else:  # Test that backend is BasicEngine object
            if not isinstance(backend, BasicEngine):
                self.next_engine = _ErrorEngine()
                raise UnsupportedEngineError(
                    "\nYou supplied a backend which is not supported,\n"
                    "i.e. not an instance of BasicEngine.\n"
                    "Did you forget the brackets to create an instance?\n"
                    "E.g. MainEngine(backend=Simulator) instead of \n"
                    "     MainEngine(backend=Simulator())"
                )
        self.backend = backend

        # default engine_list is projectq.setups.default.get_engine_list()
        if engine_list is None:
            import projectq.setups.default  # pylint: disable=import-outside-toplevel

            engine_list = projectq.setups.default.get_engine_list()

        self.mapper = None
        if isinstance(engine_list, list):
            # Test that engine list elements are all BasicEngine objects
            for current_eng in engine_list:
                if not isinstance(current_eng, BasicEngine):
                    self.next_engine = _ErrorEngine()
                    raise UnsupportedEngineError(
                        "\nYou supplied an unsupported engine in engine_list,"
                        "\ni.e. not an instance of BasicEngine.\n"
                        "Did you forget the brackets to create an instance?\n"
                        "E.g. MainEngine(engine_list=[AutoReplacer]) instead of\n"
                        "     MainEngine(engine_list=[AutoReplacer()])"
                    )
                if isinstance(current_eng, BasicMapperEngine):
                    if self.mapper is None:
                        self.mapper = current_eng
                    else:
                        self.next_engine = _ErrorEngine()
                        raise UnsupportedEngineError("More than one mapper engine is not supported.")
        else:
            self.next_engine = _ErrorEngine()
            raise UnsupportedEngineError("The provided list of engines is not a list!")
        engine_list = engine_list + [backend]

        # Test that user did not supply twice the same engine instance
        num_different_engines = len(set(id(item) for item in engine_list))
        if len(engine_list) != num_different_engines:
            self.next_engine = _ErrorEngine()
            raise UnsupportedEngineError(
                "\nError:\n You supplied twice the same engine as backend"
                " or item in engine_list. This doesn't work. Create two \n"
                " separate instances of a compiler engine if it is needed\n"
                " twice.\n"
            )

        self._qubit_idx = int(0)
        for i in range(len(engine_list) - 1):
            engine_list[i].next_engine = engine_list[i + 1]
            engine_list[i].main_engine = self
        engine_list[-1].main_engine = self
        engine_list[-1].is_last_engine = True
        self.next_engine = engine_list[0]

        # In order to terminate an example code without eng.flush
        def atexit_function(weakref_main_eng):
            eng = weakref_main_eng()
            if eng is not None:
                if not hasattr(sys, "last_type"):
                    eng.flush(deallocate_qubits=True)
                # An exception causes the termination, don't send a flush and make sure no qubits send deallocation
                # gates anymore as this might trigger additional exceptions
                else:
                    for qubit in eng.active_qubits:
                        qubit.id = -1

        self._delfun = atexit_function
        weakref_self = weakref.ref(self)
        atexit.register(self._delfun, weakref_self)

    def __del__(self):
        """
        Destroy the main engine.

        Flushes the entire circuit down the pipeline, clearing all temporary buffers (in, e.g., optimizers).
        """
        if not hasattr(sys, "last_type"):
            self.flush(deallocate_qubits=True)
        try:
            atexit.unregister(self._delfun)  # only available in Python3
        except AttributeError:  # pragma: no cover
            pass

    def set_measurement_result(self, qubit, value):
        """
        Register a measurement result

        The engine being responsible for measurement results needs to register these results with the master engine
        such that they are available when the user calls an int() or bool() conversion operator on a measured qubit.

        Args:
            qubit (BasicQubit): Qubit for which to register the measurement result.
            value (bool): Boolean value of the measurement outcome (True / False = 1 / 0 respectively).
        """
        self._measurements[qubit.id] = bool(value)

    def get_measurement_result(self, qubit):
        """
        Return the classical value of a measured qubit, given that an engine registered this result previously (see
        setMeasurementResult).

        Args:
            qubit (BasicQubit): Qubit of which to get the measurement result.

        Example:
            .. code-block:: python

                from projectq.ops import H, Measure
                from projectq import MainEngine
                eng = MainEngine()
                qubit = eng.allocate_qubit() # quantum register of size 1
                H | qubit
                Measure | qubit
                eng.get_measurement_result(qubit[0]) == int(qubit)
        """
        if qubit.id in self._measurements:
            return self._measurements[qubit.id]
        raise NotYetMeasuredError(
            "\nError: Can't access measurement result for qubit #" + str(qubit.id) + ". The problem may be:\n\t"
            "1. Your code lacks a measurement statement\n\t"
            "2. You have not yet called engine.flush() to force execution of your code\n\t"
            "3. The "
            "underlying backend failed to register the measurement result\n"
        )

    def get_new_qubit_id(self):
        """
        Returns a unique qubit id to be used for the next qubit allocation.

        Returns:
            new_qubit_id (int): New unique qubit id.
        """
        self._qubit_idx += 1
        return self._qubit_idx - 1

    def receive(self, command_list):
        """
        Forward the list of commands to the first engine.

        Args:
            command_list (list<Command>): List of commands to receive (and
                then send on)
        """
        self.send(command_list)

    def send(self, command_list):
        """
        Forward the list of commands to the next engine in the pipeline.

        It also shortens exception stack traces if self.verbose is False.
        """
        try:
            self.next_engine.receive(command_list)
        except Exception as err:  # pylint: disable=broad-except
            if self.verbose:
                raise
            exc_type, exc_value, _ = sys.exc_info()
            # try:
            last_line = traceback.format_exc().splitlines()
            compact_exception = exc_type(
                str(exc_value) + '\n raised in:\n' + repr(last_line[-3]) + "\n" + repr(last_line[-2])
            )
            compact_exception.__cause__ = None
            raise compact_exception from err  # use verbose=True for more info

    def flush(self, deallocate_qubits=False):
        """
        Flush the entire circuit down the pipeline, clearing potential buffers (of, e.g., optimizers).

        Args:
            deallocate_qubits (bool): If True, deallocates all qubits that are still alive (invalidating references to
                them by setting their id to -1).
        """
        if deallocate_qubits:
            while [qb for qb in self.active_qubits if qb is not None]:
                qb = self.active_qubits.pop()
                qb.__del__()
        self.receive([Command(self, FlushGate(), ([WeakQubitRef(self, -1)],))])
