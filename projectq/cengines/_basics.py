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

from projectq.ops import Allocate, Deallocate
from projectq.types import Qubit, Qureg
from projectq.ops import Command
import projectq.cengines


class LastEngineException(Exception):
    """
    Exception thrown when the last engine tries to access the next one.
    (Next engine does not exist)

    The default implementation of isAvailable simply asks the next engine
    whether the command is available. An engine which legally may be the last
    engine, this behavior needs to be adapted (see BasicEngine.isAvailable).
    """
    def __init__(self, engine):
        Exception.__init__(self, ("\nERROR: Sending to next engine failed. "
                                  "{} as last engine?\nIf this is legal, "
                                  "please override 'isAvailable' to adapt its"
                                  " behavior."
                                  ).format(engine.__class__.__name__))


class BasicEngine(object):
    """
    Basic compiler engine: All compiler engines are derived from this class.
    It provides basic functionality such as qubit allocation/deallocation and
    functions that provide information about the engine's position (e.g., next
    engine).

    This information is provided by the MainEngine, which initializes all
    further engines.

    Attributes:
        next_engine (BasicEngine): Next compiler engine (or the back-end).
        main_engine (MainEngine): Reference to the main compiler engine.
        is_last_engine (bool): True for the last engine, which is the back-end.
    """
    def __init__(self):
        """
        Initialize the basic engine.

        Initializes local variables such as _next_engine, _main_engine, etc. to
        None.
        """
        self.main_engine = None
        self.next_engine = None
        self.is_last_engine = False

    def is_available(self, cmd):
        """
        Default implementation of is_available:
        Ask the next engine whether a command is available, i.e.,
        whether it can be executed by the next engine(s).

        Args:
            cmd (Command): Command for which to check availability.

        Returns:
            True if the command can be executed.

        Raises:
            LastEngineException: If is_last_engine is True but is_available
                is not implemented.
        """
        if not self.is_last_engine:
            return self.next_engine.is_available(cmd)
        else:
            raise LastEngineException(self)

    def allocate_qubit(self, dirty=False):
        """
        Return a new qubit as a list containing 1 qubit object (quantum
        register of size 1).

        Allocates a new qubit by getting a (new) qubit id from the MainEngine,
        creating the qubit object, and then sending an AllocateQubit command
        down the pipeline. If dirty=True, the fresh qubit can be replaced by
        a pre-allocated one (in an unknown, dirty, initial state). Dirty qubits
        must be returned to their initial states before they are deallocated /
        freed.

        All allocated qubits are added to the MainEngine's set of active
        qubits as weak references. This allows proper clean-up at the end of
        the Python program (using atexit), deallocating all qubits which are
        still alive. Qubit ids of dirty qubits are registered in MainEngine's
        dirty_qubits set.

        Args:
            dirty (bool): If True, indicates that the allocated qubit may be
                dirty (i.e., in an arbitrary initial state).

        Returns:
            Qureg of length 1, where the first entry is the allocated qubit.
        """
        new_id = self.main_engine.get_new_qubit_id()
        qb = Qureg([Qubit(self, new_id)])
        if dirty:
            from projectq.meta import DirtyQubitTag
            if self.is_meta_tag_supported(DirtyQubitTag):
                oldnext = self.next_engine

                def cmd_modifier(cmd):
                    assert(cmd.gate == Allocate)
                    cmd.tags += [DirtyQubitTag()]
                    return cmd
                self.next_engine = projectq.cengines.CommandModifier(
                    cmd_modifier)
                self.next_engine.next_engine = oldnext
                self.send([Command(self, Allocate, (qb,))])
                self.next_engine = oldnext
                self.main_engine.active_qubits.add(qb[0])
                self.main_engine.dirty_qubits.add(qb[0].id)
                return qb

        self.send([Command(self, Allocate, (qb,))])
        self.main_engine.active_qubits.add(qb[0])
        return qb

    def allocate_qureg(self, n):
        """
        Allocate n qubits and return them as a quantum register, which is a
        list of qubit objects.

        Args:
            n (int): Number of qubits to allocate
        Returns:
            Qureg of length n, a list of n newly allocated qubits.
        """
        return Qureg([self.allocate_qubit()[0] for _ in range(n)])

    def deallocate_qubit(self, qubit):
        """
        Deallocate a qubit (and sends the deallocation command down the
        pipeline). If the qubit was allocated as a dirty qubit, add
        DirtyQubitTag() to Deallocate command.

        Args:
            qubit (BasicQubit): Qubit to deallocate.
        Raises:
            ValueError: Qubit already deallocated. Caller likely has a bug.
        """
        if qubit.id == -1:
            raise ValueError("Already deallocated.")

        from projectq.meta import DirtyQubitTag
        is_dirty = qubit.id in self.main_engine.dirty_qubits
        self.send([Command(self,
                           Deallocate,
                           (Qureg([qubit]),),
                           tags=[DirtyQubitTag()] if is_dirty else [])])

    def is_meta_tag_supported(self, meta_tag):
        """
        Check if there is a compiler engine handling the meta tag

        Args:
            engine: First engine to check (then iteratively calls
                getNextEngine)
            meta_tag: Meta tag class for which to check support

        Returns:
            supported (bool): True if one of the further compiler engines is a
            meta tag handler, i.e., engine.is_meta_tag_handler(meta_tag)
            returns True.
        """
        engine = self
        try:
            while True:
                try:
                    if engine.is_meta_tag_handler(meta_tag):
                        return True
                except AttributeError:
                    pass
                engine = engine.next_engine
        except:
            return False

    # sends the commandList to the next engine
    def send(self, command_list):
        """
        Forward the list of commands to the next engine in the pipeline.
        """
        self.next_engine.receive(command_list)


class ForwarderEngine(BasicEngine):
    """
    A ForwarderEngine is a trivial engine which forwards all commands to the
    next engine.

    It is mainly used as a substitute for the MainEngine at lower levels such
    that meta operations still work (e.g., with Compute).
    """
    def __init__(self, engine, cmd_mod_fun=None):
        """
        Initialize a ForwarderEngine.

        Args:
            engine (BasicEngine): Engine to forward all commands to.
            cmd_mod_fun (function): Function which is called before sending a
                command. Each command cmd is replaced by the command it
                returns when getting called with cmd.
        """
        BasicEngine.__init__(self)
        self.main_engine = engine.main_engine
        self.next_engine = engine
        if cmd_mod_fun is None:
            cmd_mod_fun = lambda cmd: cmd

        self._cmd_mod_fun = cmd_mod_fun

    def receive(self, command_list):
        """ Forward all commands to the next engine. """
        new_command_list = [self._cmd_mod_fun(cmd) for cmd in command_list]
        self.send(new_command_list)
