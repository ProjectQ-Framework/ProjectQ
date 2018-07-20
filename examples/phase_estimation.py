from projectq.ops import H, X, Y, Z, Tensor, QFT, get_inverse
from projectq.ops import All, Measure, QubitOperator, TimeEvolution
from projectq.meta import Control
from projectq import MainEngine

from projectq.backends import CircuitDrawer

import cmath
import numpy as np
from projectq.ops import (BasicGate)
from projectq.types import BasicQubit

def phase_estimation(eng,unitary,eigenvector,n_ancillas):

   # create the ancillas and are left to |0>
   ancilla = eng.allocate_qureg(n_ancillas)

   # Hadamard on the ancillas
   Tensor(H) | ancilla

   # Control U on the eigenvector
   unitario = unitary

   for i in range(n_ancillas):
      ipower = int(2**i)
      with Control(eng,ancilla[i]):
         for j in range(ipower):
            unitario | eigenvector 

   # Inverse QFT on the ancilla
   get_inverse(QFT) | ancilla

   # Ancilla measurement
   All(Measure) | ancilla

   # Compute the phase from the ancilla measurement (https://en.wikipedia.org/wiki/Quantum_phase_estimation_algorithm)
   fasebinlist = [int(q) for q in ancilla]
   print (fasebinlist)

   fasebin = ''.join(str(j) for j in fasebinlist)
   faseint = int(fasebin,2)
   fase = faseint / (2 ** n_ancillas)

   print (fasebin, faseint,"fase final = ", fase)
   return fase

class PhaseX(BasicGate):
   """ 
   A phase gate on X gate with
   eigenvectors H|0> and HX|0> and 
   eivenvalues exp(i2pi theta) and -exp(i2pi theta)
   """

   def __init__(self,phase):
      BasicGate.__init__(self)      
      self.phase = phase

   @property
   def matrix(self):
      theta = self.phase

      return np.matrix([[0,cmath.exp(1j * 2.0 * cmath.pi * theta)],
                        [cmath.exp(1j * 2.0 * cmath.pi * theta),0]])

   def __str__(self):
      return "PhaseX(theta)"

   def tex_str(self):
      """
      Return the Latex string representation of a PhaseX Gate.
      Returns the class name and the angle as a subscript, i.e.
      .. code-block:: latex
         [CLASSNAME]$_[ANGLE]$
      """

      return str("PhX") + "$_{" + str(self.phase) + "}$"



if __name__ == "__main__":
   #Create the compiler engine

   drawing_engine = CircuitDrawer()
   
   eng = MainEngine(drawing_engine)
##   eng = MainEngine()
   
   # Create the Unitary Operator and the eigenvector
   unitario = QubitOperator('X0 X1')
   #unitario = X
   
   ### Example ###unit = TimeEvolution(1.0,unitario)
   ### Example ###autovector = eng.allocate_qureg(2)

   ### Example ####unit = X
   ### Example ####autovector = eng.allocate_qureg(1)

   #### Defined phase with X ###

   print("Example: Defined phase with X")
   autovector = eng.allocate_qureg(1)
   X | autovector
   H | autovector
   theta = float(input ("Enter phase [0,1): "))
   unit = PhaseX(theta)
   print(type(unit))
   
   #### END Defined phase with X ###

   ### Example ###X | autovector[1]
   ### Example ####X | autovector[0]
   ### Example ###All(H) | autovector

   # Ask for the number of ancillas to use
   ene = int(input("How many ancillas?: "))
   # Call the phase_estimation function
   fase = phase_estimation(eng,unit,autovector,ene)

#======== Testing ====

   #unit | autovector
   eng.flush()
   print(drawing_engine.get_latex(),file=open("pe.tex", "w"))

#======== Testing ====   amp_after1 = eng.backend.get_amplitude('00', autovector)
#======== Testing ====   amp_after2 = eng.backend.get_amplitude('01', autovector)
#======== Testing ====   amp_after3 = eng.backend.get_amplitude('10', autovector)
#======== Testing ====   amp_after4 = eng.backend.get_amplitude('11', autovector)

#======== Testing ====   print("Amplitude saved in amp_after1: {}".format(amp_after1))
#======== Testing ====   print("Amplitude saved in amp_after2: {}".format(amp_after2))
#======== Testing ====   print("Amplitude saved in amp_after3: {}".format(amp_after3))
#======== Testing ====   print("Amplitude saved in amp_after4: {}".format(amp_after4))

   # Deferred measure del estado para que pueda imprimir cosas

   All(Measure) | autovector

   eng.flush()
   
