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

"""Exception classes for projectq.backends."""


class DeviceTooSmall(Exception):
    """Raised when a device does not have enough qubits for a desired job."""


class DeviceOfflineError(Exception):
    """Raised when a device is required but is currently offline."""


class DeviceNotHandledError(Exception):
    """Exception raised if a selected device cannot handle the circuit or is not supported by ProjectQ."""


class RequestTimeoutError(Exception):
    """Raised if a request to the job creation API times out."""


class JobSubmissionError(Exception):
    """Raised when the job creation API contains an error of some kind."""


class InvalidCommandError(Exception):
    """Raised if the backend encounters an invalid command."""


class MidCircuitMeasurementError(Exception):
    """Raised when a mid-circuit measurement is detected on a qubit."""
