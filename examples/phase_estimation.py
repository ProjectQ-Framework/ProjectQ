from projectq.ops import H, X, Y, Z, Tensor, QFT, get_inverse
from projectq.ops import All, Measure
from projectq.meta import Control
from projectq import MainEngine

from projectq.backends import CircuitDrawer, CommandPrinter

import cmath
import numpy as np
from projectq.ops import (BasicGate)

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

class PhaseXxX(BasicGate):
   """ 
   A phase gate on X (x) X : PhX(x)X gate with
   eigenvectors: |+>|+>, |+>|->,|->|+>,|->|->,  and 
   eivenvalues exp(i2pi theta) and -exp(i2pi theta)
   """

   def __init__(self,phase):
      BasicGate.__init__(self)      
      self.phase = phase

   @property
   def matrix(self):
      theta = self.phase
      
      return np.matrix([[0,0,0,cmath.exp(1j * 2.0 * cmath.pi * theta)],
                        [0,0,cmath.exp(1j * 2.0 * cmath.pi * theta),0],
                        [0,cmath.exp(1j * 2.0 * cmath.pi * theta),0,0],
                        [cmath.exp(1j * 2.0 * cmath.pi * theta),0,0,0]])

   def __str__(self):
      return "PhaseX(theta)(x)X"

   def tex_str(self):
      """
      Return the Latex string representation of a PhaseX Gate.
      Returns the class name and the angle as a subscript, i.e.
      .. code-block:: latex
         [CLASSNAME]$_[ANGLE]$
      """

      return str("PhX") + "$_{" + str(self.phase) + "}$" + str(" (x) X")




if __name__ == "__main__":

   #Create the compiler engine

#======== Testing ====   drawing_engine = CircuitDrawer()
#======== Testing ====   print_engine = CommandPrinter()
   
#======== Testing ====   eng = MainEngine(drawing_engine)

   eng = MainEngine()
   
   ### Select an example and uncomment/comment as needed ###

   #### X ###

   ####print("Example: X: Example |-> theta: .5 #ancillas:5")
   ####autovector = eng.allocate_qureg(1)
   ####X | autovector
   ####H | autovector
   ####unit = X

   #### END X ###

   #### Defined phase with X:PhX ###

   print("Example: Defined phase with PhX: Example |-> theta: .65625 (.15625) #ancillas:5")
   autovector = eng.allocate_qureg(1)
   X | autovector
   H | autovector
   theta = float(input ("Enter phase [0,1): "))
   unit = PhaseX(theta)
   
   #### END Defined phase with X:PhX ###

   #### Defined phase with PhX (x) X ###

   ####print("Example: PhX (x) X: Example |->|+> theta: .65625 (.15625) #ancillas:5")
   ####autovector = eng.allocate_qureg(2)
   ####X | autovector[0]
   ####Tensor(H) | autovector
   ####theta = float(input ("Enter phase [0,1): "))
   ####unit = PhaseXxX(theta)
   
   #### END Defined phase with PhX (x) X ###

   # Ask for the number of ancillas to use
   ene = int(input("How many ancillas?: "))

   # Call the phase_estimation function
   fase = phase_estimation(eng,unit,autovector,ene)

#======== Testing ====   eng.flush()
   
#======== Testing ====   print(drawing_engine.get_latex(),file=open("pe.tex", "w"))

#======== Testing ====   amp_after1 = eng.backend.get_amplitude('00', autovector)
#======== Testing ====   amp_after2 = eng.backend.get_amplitude('01', autovector)
#======== Testing ====   amp_after3 = eng.backend.get_amplitude('10', autovector)
#======== Testing ====   amp_after4 = eng.backend.get_amplitude('11', autovector)

#======== Testing ====   print("Amplitude saved in amp_after1: {}".format(amp_after1))
#======== Testing ====   print("Amplitude saved in amp_after2: {}".format(amp_after2))
#======== Testing ====   print("Amplitude saved in amp_after3: {}".format(amp_after3))
#======== Testing ====   print("Amplitude saved in amp_after4: {}".format(amp_after4))

   # Deferred measure of the state in order to be print

   All(Measure) | autovector

   eng.flush()
   
