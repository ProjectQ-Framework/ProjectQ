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


def _get_temporary_name():
    """
    Returns a temporary file name.
    """
    from tempfile import _get_candidate_names, _get_default_tempdir

    return "{}/{}".format(_get_default_tempdir(), next(_get_candidate_names()))


def _exec_from_file(filename, qubits, remove=True):
    """
    Executes the Python code in 'filename'.

    Args:
        filename (string): Name of the file containing the Python code.
        qubits (tuple<Qureg>): Qubits to which the permutation is being applied.
        remove (bool): Remove file after execution.
    """
    from projectq.ops import C, NOT, Toffoli, Swap, H, T, Tdag, X

    with open(filename, "r") as f:
        content = f.read()
        print(content)
        exec(content.replace("\0", ""))

    if remove:
        import os
        os.remove(filename)


class PermutationOracle:
    """
    Synthesizes a permutation using RevKit.

    Given a permutation over `2**q` elements (starting from 0), this class helps
    to automatically find a reversible circuit over `q` qubits that realizes
    that permutation.

    Example:
        .. code-block:: python
        
            PermutationOracle([0, 2, 1, 3]) | (a, b)
    """
    def __init__(self, permutation, **kwargs):
        """
        Initializes a permutation oracle.

        Args:
            permutation (list<int>): Permutation (starting from 0).

        Keyword Args:
            synth: A RevKit synthesis command which creates a reversible
                   circuit based on a reversible truth table (e.g.,
                   ``revkit.tbs`` or ``revkit.dbs``).  Can also be a 
                   nullary lambda that calls several RevKit commands.
                   **Default:** ``revkit.tbs``
        """
        self.permutation = permutation
        self.kwargs = kwargs

        self._check_permutation()

    def __or__(self, qubits):
        """
        Applies permutation to qubits (and synthesizes circuit).

        Args:
            qubits (tuple<Qureg>): Qubits to which the permutation is being applied.
        """
        try:
            import revkit
        except ModuleNotFoundError:
            raise RuntimeError(
                "The RevKit Python library needs to be installed and in the "
                "PYTHONPATH in order to call this function")

        # Convert qubits to tuple
        qs = BasicGate.make_tuple_of_qureg(qubits)

        # Permutation must have 2*q elements, where q is the number of qubits
        if 2**(len(qs)) != len(self.permutation):
            raise AttributeError(
                "Number of qubits does not fit to the size of the permutation")

        # create reversible truth table from permutation
        revkit.read_spec(permutation=" ".join(map(str, self.permutation)))

        # create reversible circuit from reversible truth table
        self.kwargs.get("synth", revkit.tbs)()

        # write reversible circuit to ProjectQ code
        filename = _get_temporary_name()
        revkit.write_projectq(filename=filename)

        # evaluate ProjectQ code in place
        _exec_from_file(filename, qs)

    def _check_permutation(self):
        """
        Checks whether permutation is valid.
        """
        # permutation must start from 0, has no duplicates and all elements are consecutive
        if sorted(list(set(self.permutation))) != list(range(len(self.permutation))):
            raise AttributeError("Invalid permutation (does it start from 0?)")
