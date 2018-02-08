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

from projectq.ops import BasicGate

from ._utils import _get_temporary_name, _exec_from_file


class PhaseOracle:
    """
    Synthesizes phase circuit from an arbitrary Boolean function.

    This creates a phase circuit from a Boolean function.  It inverts the phase
    of all amplitudes for which the function evaluates to 1.  The Boolean
    function is provided as integer representation of the function's truth table
    in binary notation.  For example, for the majority-of-three function, which
    truth table 11101000, the value for function can be, e.g., ``0b11101000,
    ``0xe8``, or ``232``.

    Example:

        This example creates a phase circuit based on the majority-of-three
        function on qubits ``a``, ``b``, and ``c``.

        .. code-block:: python

            PhaseOracle(0x8e) | (a, b, c)
    """

    def __init__(self, function, **kwargs):
        """
        Initializes a phase oracle.

        Args:
            function (int): Function truth table.

        Keyword Args:
            synth: A RevKit synthesis command which creates a reversible
                   circuit based on an And-inverter graph and requires no
                   additional ancillae (e.g.,
                   ``revkit.esopps()``).  Can also be a nullary
                   lambda that calls several RevKit commands.
                   **Default:** ``lambda: revkit.esopps()``
        """
        if isinstance(function, int):
            self.function = function
        else:
            try:
                import dormouse
                self.function = dormouse.to_truth_table(function)
            except ImportError:
                raise RuntimeError(
                    "The dormouse library needs to be installed in order to "
                    "automatically compile Python code into functions.  Try "
                    "to install dormouse with 'pip install dormouse'."
                )
        self.kwargs = kwargs

        self._check_function()

    def __or__(self, qubits):
        """
        Applies phase circuit to qubits (and synthesizes circuit).

        Args:
            qubits (tuple<Qureg>): Qubits to which the phase circuit is being applied.
        """
        try:
            import revkit
        except ImportError:
            raise RuntimeError(
                "The RevKit Python library needs to be installed and in the "
                "PYTHONPATH in order to call this function")

        # convert qubits to tuple
        qs = []
        for item in BasicGate.make_tuple_of_qureg(qubits):
            qs += item if isinstance(item, list) else [item]

        # function truth table cannot be larger than number of control qubits allow
        if 2**(2**len(qs)) <= self.function:
            raise AttributeError(
                "Function truth table exceeds number of control qubits")

        # create truth table from function integer
        revkit.tt(load="0d{}:{}".format(len(qs), self.function))

        # translate truth table into AIG
        revkit.convert(tt_to_aig = True)

        # create phase circuit from AIG
        self.kwargs.get("synth", lambda: revkit.esopps())()

        # check whether circuit has correct signature
        if revkit.ps(circuit = True, silent = True)['lines'] != len(qs):
            raise RuntimeError("Generated circuit lines does not match provided qubits")

        # write phase circuit to ProjectQ code
        filename = _get_temporary_name()
        revkit.write_projectq(filename=filename)

        # evaluate ProjectQ code in place
        _exec_from_file(filename, qs)

    def _check_function(self):
        """
        Checks whether function is valid.
        """
        # function must be positive.  We check in __or__ whether function is too large
        if self.function < 0:
            raise AttributeError("Function must be a postive integer")
