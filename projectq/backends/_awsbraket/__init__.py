# -*- coding: utf-8 -*-
#   Copyright 2021 ProjectQ-Framework (www.projectq.ch)
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

"""ProjectQ module for supporting the AWS Braket platform"""

try:
    from ._awsbraket import AWSBraketBackend
except ImportError:  # pragma: no cover

    class AWSBraketBackend:  # pylint: disable=too-few-public-methods
        """Dummy class"""

        def __init__(self, *args, **kwargs):
            raise RuntimeError(
                "Failed to import one of the dependencies required to use "
                "the Amazon Braket Backend.\n"
                "Did you install ProjectQ using the [braket] extra? "
                "(python3 -m pip install projectq[braket])"
            )
