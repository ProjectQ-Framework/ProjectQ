#   Copyright 2022 ProjectQ-Framework (www.projectq.ch)
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

"""Module containing some utility functions."""


def _rearrange_result(input_result, length):
    """Turn ``input_result`` from an integer into a bit-string.

    Args:
        input_result (int): An integer representation of qubit states.
        length (int): The total number of bits (for padding, if needed).

    Returns:
        str: A bit-string representation of ``input_result``.
    """
    return f'{input_result:0{length}b}'[::-1]
