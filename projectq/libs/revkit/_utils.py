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
        exec(f.read().replace("\0", ""))

    if remove:
        import os
        os.remove(filename)
