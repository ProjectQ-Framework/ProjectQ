from projectq import MainEngine
from projectq.ops import H, CX, All, Measure
from projectq.cengines import BasicMapperEngine

from projectq.backends import AzureQuantumBackend

azure_quantum_backend = AzureQuantumBackend(
    provider='ionq',
    target_name='ionq.simulator',
    resource_id="/subscriptions/932822b4-f75e-400b-a4a9-c0c1da7acf98/resourceGroups/sachadar-quantum-dev"
                "/providers/Microsoft.Quantum/Workspaces/sachadar-quantum-workspace",
    location="East US"
)

mapper = BasicMapperEngine()
max_qubits = 10

mapping = {}
for i in range(max_qubits):
    mapping[i] = i

mapper.current_mapping = mapping

main_engine = MainEngine(
    backend=azure_quantum_backend,
    engine_list=[mapper]
)

circuit = main_engine.allocate_qureg(3)
q0, q1, q2 = circuit

H | q0
CX | (q0, q1)
CX | (q1, q2)
All(Measure) | circuit

main_engine.flush()
print(azure_quantum_backend.get_probabilities(circuit))
