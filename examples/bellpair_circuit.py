# -*- coding: utf-8 -*-
# pylint: skip-file

import matplotlib.pyplot as plt

from projectq import MainEngine
from projectq.backends import CircuitDrawer
from projectq.setups.default import get_engine_list
from projectq.libs.hist import histogram

from teleport import create_bell_pair

# create a main compiler engine
drawing_engine = CircuitDrawer()
eng = MainEngine(engine_list=get_engine_list() + [drawing_engine])

qb0, qb1 = create_bell_pair(eng)

eng.flush()
print(drawing_engine.get_latex())

histogram(eng.backend, [qb0, qb1])
plt.show()
