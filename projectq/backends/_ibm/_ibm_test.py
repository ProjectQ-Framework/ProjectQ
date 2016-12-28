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

"""Tests for projectq.backends._ibm._ibm.py."""

import pytest

from projectq import MainEngine
from projectq.cengines import (TagRemover,
                               LocalOptimizer,
                               AutoReplacer,
                               IBMCNOTMapper,
                               DummyEngine)
from projectq.ops import (Command, X, Y, Z, T, Tdag, S, Sdag, CNOT, Measure,
                          Allocate, Deallocate, NOT, Rx, Entangle)

from projectq.backends._ibm import _ibm


# Insure that no HTTP request can be made in all tests in this module
@pytest.fixture(autouse=True)
def no_requests(monkeypatch):
    monkeypatch.delattr("requests.sessions.Session.request")


_api_url = 'https://qcwi-staging.mybluemix.net/api/'
_api_url_status = 'https://quantumexperience.ng.bluemix.net/api/'


@pytest.mark.parametrize("single_qubit_gate, is_available", [
	(X, True), (Y, True), (Z, True), (T, True), (Tdag, True), (S, True),
	(Sdag, True), (Allocate,True), (Deallocate, True), (Measure, True),
	(NOT, True), (Rx(0.5), False)])
def test_ibm_backend_is_available(single_qubit_gate, is_available):
	eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
	qubit1 = eng.allocate_qubit()
	ibm_backend = _ibm.IBMBackend()
	cmd = Command(eng, single_qubit_gate , (qubit1,))
	assert ibm_backend.is_available(cmd) == is_available


@pytest.mark.parametrize("num_ctrl_qubits, is_available", [
	(0, True), (1, True), (2, False), (3, False)])
def test_ibm_backend_is_available_control_not(num_ctrl_qubits, is_available):
	eng = MainEngine(backend=DummyEngine(), engine_list=[DummyEngine()])
	qubit1 = eng.allocate_qubit()
	qureg = eng.allocate_qureg(num_ctrl_qubits)
	print(len(qureg))
	ibm_backend = _ibm.IBMBackend()
	cmd = Command(eng, NOT , (qubit1,))
	cmd.add_control_qubits(qureg)
	print(cmd)
	assert ibm_backend.is_available(cmd) == is_available


def test_ibm_backend_functional_test(monkeypatch):
	from projectq.setups.decompositions import (crz2cxandrz,
                                            r2rzandph,
                                            ph2r,
                                            globalphase,
                                            swap2cnot,
                                            toffoli2cnotandtgate,
                                            entangle,
                                            qft2crandhadamard)
	correct_info = '{"playground":[{"line":0,"name":"q","gates":[{"position":0,"name":"h"},{"position":3,"name":"h"},{"position":4,"name":"measure"}]},{"line":1,"name":"q","gates":[{"position":0,"name":"h"},{"position":2,"name":"h"},{"position":3,"name":"measure"}]},{"line":2,"name":"q","gates":[{"position":1,"name":"cx","to":1},{"position":2,"name":"cx","to":0},{"position":3,"name":"h"},{"position":4,"name":"measure"}]},{"line":3,"name":"q","gates":[]},{"line":4,"name":"q","gates":[]}],"numberColumns":40,"numberLines":5,"numberGates":200,"hasMeasures":true,"topology":"250e969c6b9e68aa2a045ffbceb3ac33"}'
	# patch send 
	def mock_send(*args, **kwargs):
		assert args[0] == correct_info
		return {'data': {'qasm': 'qreg q,5;gate h, [[0.7071067811865476,0.7071067811865476],[0.7071067811865476,-0.7071067811865476]];gate measure, [[1,0],[0,0.7071067811865476+0.7071067811865476i]];gate cx, [[1,0,0,0],[0,1,0,0],[0,0,0,1],[0,0,1,0]];\nh q[0];h q[1];cx q[1], q[2];h q[1];cx q[0], q[2];h q[0];measure q[1];h q[2];measure q[0];measure q[2];', 'p': {'values': [0.4580078125, 0.0068359375, 0.013671875, 0.064453125, 0.048828125, 0.0234375, 0.013671875, 0.37109375], 'qubits': [0, 1, 2], 'labels': ['000', '001', '010', '011', '100', '101', '110', '111']}, 'time': 16.12812304496765, 'serialNumberDevice': 'Real5Qv1'}, 'date': '2016-12-27T01:04:04.395Z'}
	monkeypatch.setattr(_ibm, "send", mock_send)

	backend = _ibm.IBMBackend()
	engine_list = [TagRemover(), LocalOptimizer(10), AutoReplacer(), 
	               TagRemover(), IBMCNOTMapper(), LocalOptimizer(10)]
	eng = MainEngine(backend=backend, engine_list=engine_list)
	qureg = eng.allocate_qureg(3)
	# entangle the qureg
	Entangle | qureg
	# measure; should be all-0 or all-1
	Measure | qureg
	# run the circuit
	eng.flush()

