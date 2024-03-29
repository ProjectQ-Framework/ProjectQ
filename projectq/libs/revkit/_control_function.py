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

"""RevKit support for control function oracles."""


from projectq.ops import BasicGate

from ._utils import _exec


class ControlFunctionOracle:  # pylint: disable=too-few-public-methods
    """
    Synthesize a negation controlled by an arbitrary control function.

    This creates a circuit for a NOT gate which is controlled by an arbitrary
    Boolean control function.  The control function is provided as integer
    representation of the function's truth table in binary notation.  For
    example, for the majority-of-three function, which truth table 11101000,
    the value for function can be, e.g., ``0b11101000``, ``0xe8``, or ``232``.

    Example:
        This example creates a circuit that causes to invert qubit ``d``,
        the majority-of-three function evaluates to true for the control
        qubits ``a``, ``b``, and ``c``.

        .. code-block:: python

            ControlFunctionOracle(0x8E) | ([a, b, c], d)
    """

    def __init__(self, function, **kwargs):
        """
        Initialize a control function oracle.

        Args:
            function (int): Function truth table.

        Keyword Args:
            synth: A RevKit synthesis command which creates a reversible
                   circuit based on a truth table and requires no additional
                   ancillae (e.g., ``revkit.esopbs``).  Can also be a nullary
                   lambda that calls several RevKit commands.
                   **Default:** ``revkit.esopbs``
        """
        if isinstance(function, int):
            self.function = function
        else:
            try:
                import dormouse  # pylint: disable=import-outside-toplevel

                self.function = dormouse.to_truth_table(function)
            except ImportError as err:  # pragma: no cover
                raise RuntimeError(
                    "The dormouse library needs to be installed in order to "
                    "automatically compile Python code into functions.  Try "
                    "to install dormouse with 'pip install dormouse'."
                ) from err
        self.kwargs = kwargs

        self._check_function()

    def __or__(self, qubits):
        """
        Apply control function to qubits (and synthesizes circuit).

        Args:
            qubits (tuple<Qureg>): Qubits to which the control function is
                                   being applied. The first `n` qubits are for
                                   the controls, the last qubit is for the
                                   target qubit.
        """
        try:
            import revkit  # pylint: disable=import-outside-toplevel
        except ImportError as err:  # pragma: no cover
            raise RuntimeError(
                "The RevKit Python library needs to be installed and in the "
                "PYTHONPATH in order to call this function"
            ) from err
        # pylint: disable=invalid-name

        # convert qubits to tuple
        qs = []
        for item in BasicGate.make_tuple_of_qureg(qubits):
            qs += item if isinstance(item, list) else [item]

        # function truth table cannot be larger than number of control qubits
        # allow
        if 2 ** (2 ** (len(qs) - 1)) <= self.function:
            raise AttributeError("Function truth table exceeds number of control qubits")

        # create truth table from function integer
        hex_length = max(2 ** (len(qs) - 1) // 4, 1)
        revkit.tt(table=f"{self.function:#0{hex_length}x}")

        # create reversible circuit from truth table
        self.kwargs.get("synth", revkit.esopbs)()

        # check whether circuit has correct signature
        if revkit.ps(mct=True, silent=True)['qubits'] != len(qs):
            raise RuntimeError("Generated circuit lines does not match provided qubits")

        # convert reversible circuit to ProjectQ code and execute it
        _exec(revkit.to_projectq(mct=True), qs)

    def _check_function(self):
        """Check whether function is valid."""
        # function must be positive. We check in __or__ whether function is
        # too large
        if self.function < 0:
            raise AttributeError("Function must be a positive integer")
