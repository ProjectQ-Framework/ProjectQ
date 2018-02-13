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

import projectq
from projectq.cengines import BasicEngine
from projectq.ops import Command, FlushGate
from projectq.types import WeakQubitRef
from projectq.backends import Simulator


class NotYetMeasuredError(Exception):
    pass


class UnsupportedEngineError(Exception):
    pass


class MainEngine(BasicEngine):
    """
    The MainEngine class provides all functionality of the main compiler
    engine.

    It initializes all further compiler engines (calls, e.g.,
    .next_engine=...) and keeps track of measurement results and active
    qubits (and their IDs).

    Attributes:
        next_engine (BasicEngine): Next compiler engine (or the back-end).
        main_engine (MainEngine): Self.
        active_qubits (WeakSet): WeakSet containing all active qubits
        dirty_qubits (Set): Containing all dirty qubit ids
        backend (BasicEngine): Access the back-end.

    """
    def __init__(self, backend=None, engine_list=None, setup=None,
                 verbose=False):
        """
        Initialize the main compiler engine and all compiler engines.

        Sets 'next_engine'- and 'main_engine'-attributes of all compiler
        engines and adds the back-end as the last engine.

        Args:
            backend (BasicEngine): Backend to send the circuit to.
            engine_list (list<BasicEngine>): List of engines / backends to use
                as compiler engines.
            setup (module): Setup module which defines a function called
                `get_engine_list()`. `get_engine_list()` returns the list
                of engines to be used as compiler engines.
                The default setup is `projectq.setups.default` (if no engine
                list and no setup is provided).
            verbose (bool): Either print full or compact error messages.
                            Default: False (i.e. compact error messages).

        Example:
            .. code-block:: python

                from projectq import MainEngine
                eng = MainEngine() # uses default setup and the Simulator

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
        BasicEngine.__init__(self)

        if backend is None:
            backend = Simulator()
        else:  # Test that backend is BasicEngine object
            if not isinstance(backend, BasicEngine):
                raise UnsupportedEngineError(
                    "\nYou supplied a backend which is not supported,\n"
                    "i.e. not an instance of BasicEngine.\n"
                    "Did you forget the brackets to create an instance?\n"
                    "E.g. MainEngine(backend=Simulator) instead of \n"
                    "     MainEngine(backend=Simulator())")
        # default setup is projectq.setups.default
        if engine_list is None and setup is None:
            import projectq.setups.default
            setup = projectq.setups.default

        if not (engine_list is None or setup is None):  # can't provide both
            raise ValueError("\nPlease provide either a setup or an engine "
                             "list, but not both.")

        if engine_list is None:
            engine_list = setup.get_engine_list()

        if isinstance(engine_list, list):
            # Test that engine list elements are all BasicEngine objects
            for current_eng in engine_list:
                if not isinstance(current_eng, BasicEngine):
                    raise UnsupportedEngineError(
                        "\nYou supplied an unsupported engine in engine_list,"
                        "\ni.e. not an instance of BasicEngine.\n"
                        "Did you forget the brackets to create an instance?\n"
                        "E.g. MainEngine(engine_list=[AutoReplacer]) instead "
                        "of\n     MainEngine(engine_list=[AutoReplacer()])")
        else:
            raise UnsupportedEngineError(
                "The provided list of engines is not a list!")
        engine_list = engine_list + [backend]
        self.backend = backend

        # Test that user did not supply twice the same engine instance
        num_different_engines = len(set([id(item) for item in engine_list]))
        if len(engine_list) != num_different_engines:
            raise UnsupportedEngineError(
                "\nError:\n You supplied twice the same engine as backend"
                " or item in engine_list. This doesn't work. Create two \n"
                " separate instances of a compiler engine if it is needed\n"
                " twice.\n")

        self._qubit_idx = int(0)
        for i in range(len(engine_list) - 1):
            engine_list[i].next_engine = engine_list[i + 1]
            engine_list[i].main_engine = self
        engine_list[-1].main_engine = self
        engine_list[-1].is_last_engine = True
        self.next_engine = engine_list[0]
        self.main_engine = self
        self.active_qubits = weakref.WeakSet()
        self._measurements = dict()
        self.dirty_qubits = set()
        self.verbose = verbose

        # In order to terminate an example code without eng.flush
        def atexit_function(weakref_main_eng):
            eng = weakref_main_eng()
            if eng is not None:
                if not hasattr(sys, "last_type"):
                    eng.flush(deallocate_qubits=True)
                # An exception causes the termination, don't send a flush and
                # make sure no qubits send deallocation gates anymore as this
                # might trigger additional exceptions
                else:
                    for qubit in eng.active_qubits:
                        qubit.id = -1

        self._delfun = atexit_function
        weakref_self = weakref.ref(self)
        atexit.register(self._delfun, weakref_self)

    def __del__(self):
        """
        Destroy the main engine.

        Flushes the entire circuit down the pipeline, clearing all temporary
        buffers (in, e.g., optimizers).
        """
        if not hasattr(sys, "last_type"):
            self.flush(deallocate_qubits=True)
        try:
            atexit.unregister(self._delfun)  # only available in Python3
        except AttributeError:
            pass

    def set_measurement_result(self, qubit, value):
        """
        Register a measurement result

        The engine being responsible for measurement results needs to register
        these results with the master engine such that they are available when
        the user calls an int() or bool() conversion operator on a measured
        qubit.

        Args:
            qubit (BasicQubit): Qubit for which to register the measurement
                result.
            value (bool): Boolean value of the measurement outcome
                (True / False = 1 / 0 respectively).
        """
        self._measurements[qubit.id] = bool(value)

    def get_measurement_result(self, qubit):
        """
        Return the classical value of a measured qubit, given that an engine
        registered this result previously (see setMeasurementResult).

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
        else:
            raise NotYetMeasuredError(
                "\nError: Can't access measurement result for "
                "qubit #" + str(qubit.id) + ". The problem may "
                "be:\n\t1. Your "
                "code lacks a measurement statement\n\t"
                "2. You have not yet called engine.flush() to "
                "force execution of your code\n\t3. The "
                "underlying backend failed to register "
                "the measurement result\n")

    def get_new_qubit_id(self):
        """
        Returns a unique qubit id to be used for the next qubit allocation.

        Returns:
            new_qubit_id (int): New unique qubit id.
        """
        self._qubit_idx += 1
        return (self._qubit_idx - 1)

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
        except:
            if self.verbose:
                raise
            else:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                # try:
                last_line = traceback.format_exc().splitlines()
                compact_exception = exc_type(str(exc_value) +
                                             '\n raised in:\n' +
                                             repr(last_line[-3]) +
                                             "\n" + repr(last_line[-2]))
                compact_exception.__cause__ = None
                raise compact_exception  # use verbose=True for more info

    def flush(self, deallocate_qubits=False):
        """
        Flush the entire circuit down the pipeline, clearing potential buffers
        (of, e.g., optimizers).

        Args:
            deallocate_qubits (bool): If True, deallocates all qubits that are
                still alive (invalidating references to them by setting their
                id to -1).
        """
        if deallocate_qubits:
            while len(self.active_qubits):
                qb = self.active_qubits.pop()
                qb.__del__()
        self.receive([Command(self, FlushGate(), ([WeakQubitRef(self, -1)],))])
