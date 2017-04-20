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
Defines the QubitPlacementTag meta tag.
"""


class QubitPlacementTag(object):
    """
    Qubit placement meta tag
    """
    def __init__(self, position):
        self.position = position

    def __eq__(self, other):
        return (isinstance(other, QubitPlacementTag)
                and self.position == other.position)

    def __ne__(self, other):
        return not self.__eq__(other)
