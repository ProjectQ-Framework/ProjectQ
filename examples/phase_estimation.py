from projectq.ops import H, X, Y, Z, Tensor, QFT, get_inverse, All, Measure, QubitOperator, C, T, S, Tdag, Sdag
from projectq import MainEngine

def phase_estimation(eng,unitary,eigenvector,n_ancillas):

   # create the ancillas and are left to |0>
   ancilla = eng.allocate_qureg(n_ancillas)

   # Hadamard on the ancillas
   Tensor(H) | ancilla

   # Control U on the eigenvector
   unitario = unitary

   for i in range(n_ancillas):
      C(unitario) | (ancilla[i],eigenvector)
      for j in range(i):
         C(unitario) | (ancilla[i],eigenvector)

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
   autovector = eng.allocate_qureg(2)
   X | autovector[1]
   All(H) | autovector

   # Ask for the number of ancillas to use
   ene = int(input("How many ancillas?: "))
   # Call the phase_estimation function
   fase = phase_estimation(eng,unitario,autovector,ene)


   # Deferred measure del estado para que pueda imprimir cosas

   All(Measure) | autovector

   eng.flush()
