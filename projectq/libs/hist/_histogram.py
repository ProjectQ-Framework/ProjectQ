import matplotlib.pyplot as plt
from projectq.backends import Simulator

def histogram(sim, qureg):
    #qubit_ids = set()
    #for qb in qubit_list:
    #qubit_ids.add(qb.id)
    qubit_list = []
    for q in qureg:
        if(isinstance(q, list)):
            for qb in q:
                qubit_list.append(qb)
        else:
            qubit_list.append(q)
    if len(qubit_list) > 5:
        print(f'Warning: For {len(qubit_list)} qubits there are 2^{len(qubit_list)} different outcomes')
        print("The resulting histogram may look bad and/or take too long")
        print("Consider calling histogram() with a sublist of the qubits", flush=True)
    outcome = [0] * len(qubit_list)
    n_outcomes = (1 << len(qubit_list))
    probabilities = {}
    for i in range (n_outcomes):
        for pos in range (len(qubit_list)):
            if((1 << pos) & i):
                outcome[pos] = 1
            else:
                outcome[pos] = 0
        str1 = ""
        probabilities[''.join([str(bit) for bit in outcome])] = sim.get_probability(outcome, qubit_list)
    fig, axes = plt.subplots(figsize = (min(21.2, 2 + 0.6 * (1 << len(qubit_list))), 7))
    names = list(probabilities.keys())
    values = list(probabilities.values())
    axes.bar(names, values)
    fig.suptitle('Measurement Probabilities')
    plt.show()
    return(fig, axes, probabilities)
