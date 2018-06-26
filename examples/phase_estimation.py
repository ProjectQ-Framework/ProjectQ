from projectq.ops import H, X, Y, Z, Tensor, QFT, get_inverse, Measure, C, T, S, Tdag, Sdag
from projectq import MainEngine

def phase_estimation(eng,unitary,eigenvector,n_ancillas):

   # create the ancillas and are left to |0>
   ancilla = eng.allocate_qureg(n_ancillas)

   # Hadamard on the ancillas
   Tensor(H) | ancilla

   # Control U on the eigenvector
   # Por ahora solo funciona con unitary = X *************
   unitario = X # ****** unitary
   for i in range(n_ancillas):
      if i %2 == 0:
         C(unitario) | (ancilla[i],eigenvector[0])
      else:
         pass

   # Inverse QFT on the ancilla
   get_inverse(QFT) | ancilla

   # Ancilla measurement
   Measure | ancilla

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
   unitario = X
   autovector = eng.allocate_qureg(1)
   X | autovector[0]
   H | autovector[0]

   # Ask for the number of ancillas to use
   ene = int(input("How many ancillas?: "))
   # Call the phase_estimation function
   fase = phase_estimation(eng,unitario,autovector,ene)


   # Deferred measure del estado para que pueda imprimir cosas

   Measure | autovector

   eng.flush()
