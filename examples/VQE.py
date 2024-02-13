## ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Variational Quantum Eigensolver
## ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

import projectq as pq
from projectq import MainEngine
from projectq.ops import QubitOperator, Measure, All, Rx, Ry

import numpy as np, cmath
from scipy.optimize import minimize


class VQE(object):

    def __init__(self, minimiser = minimize,
                       min_args = [], 
                       min_kwargs = {'method': 'Nelder-Mead'}):
        ''' Set up minimiser to be used in main VQE algorithm. Default is scipy's optimize.minimize with Nelder-Mead method. 
            
            Parameters:
            
            \minimiser : (function(objective, x0, *args, **kwargs)) a minimising function whose first two arguments should be the objective function to be minimised and initial parameter guesses, followed by *args and **kwargs as desired. 
            (User should create a wrapper for their minimising function of choice if it doesn't suit the above requirements.)
            
            \min_args : (list) arguments to be passed to \minimiser in form of *args (see \minimiser above).
            
            \min_kwargs : (dict) arguments to be passed to \minimiser in form of **kwargs (see \minimiser above).
            
            '''
        
        self.minimiser = minimiser
        self.min_args = min_args
        self.min_kwargs = min_kwargs
        
    def run(self, ansatz, hamiltonian, initial_params,
            draws = 10000, engine = MainEngine(), verbose = None,
            callback = 'callback', full_output = False):
        ''' Main function; applies the VQE algorithm with the given parameters and arguments using the minimising function set up in self.__init__(...). Finds the parameters that create a state using \ansatz with the lowest possible expectation value for the operator \hamiltonian.
            
            Params:
            
            \ansatz : (function: params, engine -> qureg) function that prepares the state whose expectation in \hamiltonian we want to calculate, given parameters and an engine. Should return a qubit register created using the provided engine with the state prepared.
            
            \hamiltonian : (QubitOperator) operator for which we want to calculate the expectation.
            
            \initial_params : (list) initial parameters to be provided to the minimising function.
            
            \draws : (int) number of times to sample in calculating expectation 
            
            \engine : (?) an Engine object to use.
            
            \verbose : (bool or function) if True, prints iteration params and expectation every iteration. if a function, is passed to the \callback method of the minimiser.
            
            \callback : (str) argument of minimiser to pass \verbose to.
            
            \full_output : (bool) whether to return final result as well as each iteration's params and expectations (True) or just the final result (None).
            
            '''
        
        # Handle arguments
        types = [QubitOperator, list, int, MainEngine, str, bool]
        args = [hamiltonian, initial_params, draws, engine, callback, full_output]
        argstr = ['hamiltonian', 'initial_params', 'draws', 'engine', 'callback', 'full_output']
        
        for i, arg in enumerate(args):
            if not isinstance(arg, types[i]):
                raise TypeError('Argument `%s` provided to expectation must be a %s' % (argstr[i], types[i].__name__))
        
        if draws <= 0:
            raise ValueError('Argument `draws` provided to expectation must be positive.')
        
        if not callable(ansatz):
            raise TypeError('Argument `ansatz` provided to expectation must be a function of two arguments - the state preparation parameters and a QC engine.')
        
        # Prepare objective function
        self.exp_calls = []
        self.param_calls = []
        def obj(params):
            ''' Exploit fact that minimiser calls this every time to store calculated expectation in each iteration. '''
            
            exp = self.expectation(lambda eng: ansatz(params, eng),
                                   hamiltonian, draws, engine)
            
            self.exp_calls.append(exp)
            self.param_calls.append(params)
            
            return exp
        
        # Prepare verbose function
        self.iter = 0
        self.iter_params = []
        self.iter_exps = []
        
        def verb_func(params):
            ''' `callback` argument in scipy.optimize.minimize is called each iteration with current params as args. Exploit this. '''
            
            self.iter += 1
            self.iter_params.append(params)
            self.iter_exps.append(self.exp_calls[-1])
            
            print('Iteration %i: \n  Params:' % self.iter, params, '\n  Expectation:', self.iter_exps[-1])
        
        # Apply
        argnames = self.minimiser.__code__.co_varnames
        if callback in argnames and verbose is not None:
            if verbose is True:
                self.min_kwargs[callback] = verb_func
            else:
                self.min_kwargs[callback] = verbose
        
        final = self.minimiser(obj, initial_params,
                               *self.min_args,
                               **self.min_kwargs)
        
        if full_output:
            return final, (self.iter_params, self.iter_exps), (self.param_calls, self.exp_calls)
        
        return final
        
    @staticmethod
    def even_ones(integer, relevant_inds):
        ''' Counts number of ones in \integer in the spots indicated by \relevant_inds. Returns true if even, false if odd.
            
            Parameters:
            
            \integer : (int) number whose ones we want to count.
            
            \relevant_inds : (list) list of ints representing the indices in \integer whose ones we want to count.
            
            '''
        
        # Integer with ones in the relevant inds
        ones_rel_inds = 0
        for ind in relevant_inds:
            ones_rel_inds += 10**ind
        
        # Count 1s in relevant inds by counting 2s in sum of \integer and ones_rel_inds
        n_ones = str(integer + ones_rel_inds).count('2')
        
        return n_ones % 2 == 0
        
    
    def expectation(self, prep_state, operator, draws, engine):
        ''' Measures, by sampling \draws times, the expectation value of the operator \operator in the state prepared by applying \prep_state on the initial state of all 0s (|000...>).
        
            Parameters:
            
            \prep_state : (function) takes in a QC engine, creates a qubit register and applies a series of operations on it. Returns the qubit register.
            
            \operator : (QubitOperator) operator whose expectation in state prepared by \prep_state we want to measure.
            
            \draws : (int) number of times we will sample to get expectation.
            
            \eng : (MainEngine) a quantum computing engine.
            
            '''
        
        # Get expectation, term by term
        ''' Each term in the operator will be made of Is, Xs, Ys and Zs. Measuring X is the same as rotating -pi/2 around Y and measuring Z. Measuring Y is the same as rotating +pi/2 around X and measuring Z. And measuring Z is just measuring Z. 
            We build the expectation by applying the relevant rotations to the prepared state, then measuring in the Z basis. Repeating this process many times builds a sample we can calculate expectations from. '''
        expectation = 0
        for term, coef in operator.terms.items():
            
            rotations = []
            qubits_of_interest = []
            
            # If term is identity, add one to expectation
            if term == (): 
                expectation += coef
                continue
            
            # Else, get corresponding rotations
            for qubit, op in term:
                
                qubits_of_interest.append(qubit)
                
                if op == 'X':
                    rotations.append((Ry(-np.pi/2), qubit))
                elif op == 'Y':
                    rotations.append((Rx(np.pi/2), qubit))
            
            # Get expectation from sampling
            results = {}
            for _ in range(draws):
                
                # Prepare state
                qureg = prep_state(engine)

                # Apply rotations
                for rot, q in reversed(rotations):
                    rot | qureg[q]

                # Measure
                All(Measure) | qureg
                engine.flush()

                # Results
                result = int(''.join(str(int(q)) for q in reversed(qureg)))#, base = 2)
                results[result] = results.get(result, 0) + 1

            # Process results
            ''' Our result is a string of 0s and 1s, for every qubit used. The result is the product of the eigenvalue of each qubit of interest (+1 for measured 0s, -1 for measured 1s). Thus, we count the 1s measured in our qubits of interest and check whether there's an even or odd number of them. This is equivalent to checking the parity of the result in the (qu)bits of interest. 
                Thus, if parity is even, result is +1, else -1. We add the corresponding result to the expectation.
                '''
            for result, count in results.items():

                # Get parity
                if self.even_ones(result, qubits_of_interest):
                    parity = 1
                else:
                    parity = -1

                # Add to expectation
                expectation += parity * coef * count / draws
        
        return expectation














## Test
## ~~~~

if __name__ == "__main__":
    
    from projectq.ops import H, X
    import time
    
    print('\nTesting VQE:')
    
    from scipy.optimize import minimize
    vqe = VQE(minimize, [], {'method': 'Nelder-Mead'})
    
    def ansatz(params, eng):
        qureg = eng.allocate_qureg(1)
        Ry(params[0]) | qureg[0]
        return qureg
    
    hamiltonian = QubitOperator('Z0')
    
    start = time.time()
    result = vqe.run(ansatz, hamiltonian, [3],
                    verbose = True, callback = 'callback', full_output = True)
    
    print('\nRan in', int(time.time() - start), 'seconds, with result', result[0]['x'], ':')
    print(result[0])
    
    print('\nDone in', len(result[1][0]), 'iterations:')
    print('Iter, Params, Exp:')
    for i in range(len(result[1][0])):
        print(i, result[1][0][i], result[1][1][i])