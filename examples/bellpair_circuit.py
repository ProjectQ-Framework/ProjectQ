# -*- coding: utf-8 -*-
# pylint: skip-file

"""Example implementation of a quantum circuit generating a Bell pair state."""

import matplotlib.pyplot as plt
from teleport import create_bell_pair

from projectq import MainEngine
from projectq.backends import CircuitDrawer
from projectq.libs.hist import histogram
from projectq.setups.default import get_engine_list

# create a main compiler engine
drawing_engine = CircuitDrawer()
eng = MainEngine(engine_list=get_engine_list() + [drawing_engine])

qb0, qb1 = create_bell_pair(eng)

eng.flush()
print(drawing_engine.get_latex())

histogram(eng.backend, [qb0, qb1])
plt.show()
