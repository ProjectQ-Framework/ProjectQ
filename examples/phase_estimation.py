from projectq.ops import H, X, Y, Z, Tensor, QFT, get_inverse
from projectq.ops import All, Measure, QubitOperator, TimeEvolution
from projectq.meta import Control
from projectq import MainEngine

def phase_estimation(eng,unitary,eigenvector,n_ancillas):

   # create the ancillas and are left to |0>
   ancilla = eng.allocate_qureg(n_ancillas)

   # Hadamard on the ancillas
   Tensor(H) | ancilla

   # Control U on the eigenvector
   unitario = unitary

   for i in range(n_ancillas):
      with Control(eng,ancilla[i]):
         unitario | eigenvector
      for j in range(i):
         with Control(eng,ancilla[i]):
            unitario | eigenvector

   # Inverse QFT on the ancilla
   get_inverse(QFT) | ancilla

   # Ancilla measurement
   All(Measure) | ancilla

   # Compute the phase from the ancilla measurement (https://en.wikipedia.org/wiki/Quantum_phase_estimation_algorithm)
   fasebinlist = [int(q) for q in ancilla]
   print (fasebinlist, type(fasebinlist))

   fasebin = ''.join(str(j) for j in fasebinlist)
   faseint = int(fasebin,2)
   fase = faseint / (2 ** n_ancillas)

   print (fasebin, faseint,"fase final = ", fase)
   return fase



if __name__ == "__main__":
   #Create the compiler engine
   eng = MainEngine()
   
   # Create the Unitary Operator and the eigenvector
   unitario = QubitOperator('X0 X1')
   #unitario = X
   
   unit = TimeEvolution(1.0,unitario)

   autovector = eng.allocate_qureg(2)
   X | autovector[1]
   All(H) | autovector

   # Ask for the number of ancillas to use
   ene = int(input("How many ancillas?: "))
   # Call the phase_estimation function
   fase = phase_estimation(eng,unit,autovector,ene)

#======== Testing ====

   #unit | autovector
   eng.flush()
   amp_after1 = eng.backend.get_amplitude('00', autovector)
   amp_after2 = eng.backend.get_amplitude('01', autovector)
   amp_after3 = eng.backend.get_amplitude('10', autovector)
   amp_after4 = eng.backend.get_amplitude('11', autovector)

   print("Amplitude saved in amp_after1: {}".format(amp_after1))
   print("Amplitude saved in amp_after2: {}".format(amp_after2))
   print("Amplitude saved in amp_after3: {}".format(amp_after3))
   print("Amplitude saved in amp_after4: {}".format(amp_after4))

   # Deferred measure del estado para que pueda imprimir cosas

   All(Measure) | autovector

   eng.flush()
