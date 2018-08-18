#   Copyright 2018 ProjectQ-Framework (www.projectq.ch)
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""Tests for projectq.ops._phase_estimation."""

import copy
import cmath
import numpy as np
import pytest

from projectq import MainEngine
from projectq.ops import H, X, Y, Z, Tensor, QFT, get_inverse,StatePreparation
from projectq.ops import All, Measure

from projectq.ops import (BasicGate)

from projectq.ops import _phase_estimation as pe


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


def simple_test_X_eigenvectors():
   eng = MainEngine()
   results = np.array([])
   for i in range(10):
      autovector = eng.allocate_qureg(1)
      X | autovector
      H | autovector
      unit = X
      ancillas = eng.allocate_qureg(1)
      pe.PhaseEstimation(unit) | (ancillas,autovector)
      get_inverse(QFT) | ancillas
      All(Measure) | ancillas
      fasebinlist = [int(q) for q in ancillas]
      fasebin = ''.join(str(j) for j in fasebinlist)
      faseint = int(fasebin,2)
      phase = faseint / (2. ** (len(ancillas)))
      results = np.append(results,phase)
      All(Measure) | autovector
      eng.flush()
      
   perc_95 = np.percentile(results,95)
   assert perc_95 == 0.5
   
def test_phaseX_eigenvectors_minus():
   eng = MainEngine()
   results = np.array([])
   for i in range(10):
      autovector = eng.allocate_qureg(1)
      X | autovector
      H | autovector
      theta = .15625
      unit = PhaseX(theta)
      ancillas = eng.allocate_qureg(5)
      pe.PhaseEstimation(unit) | (ancillas,autovector)
      get_inverse(QFT) | ancillas
      All(Measure) | ancillas
      fasebinlist = [int(q) for q in ancillas]
      fasebin = ''.join(str(j) for j in fasebinlist)
      faseint = int(fasebin,2)
      phase = faseint / (2. ** (len(ancillas)))
      results = np.append(results,phase)
      All(Measure) | autovector
      eng.flush()
      
   perc_75 = np.percentile(results,75)
   assert perc_75 == pytest.approx(.65625, abs=1e-2), "Percentile 75 not as expected (%f)" % (perc_75)

def test_phaseXxX_eigenvectors_minusplus():
   eng = MainEngine()
   results = np.array([])
   for i in range(10):
      autovector = eng.allocate_qureg(2)
      X | autovector[0]
      Tensor(H) | autovector
      theta = .15625
      unit = PhaseXxX(theta)
      ancillas = eng.allocate_qureg(5)
      pe.PhaseEstimation(unit) | (ancillas,autovector)
      get_inverse(QFT) | ancillas
      All(Measure) | ancillas
      fasebinlist = [int(q) for q in ancillas]
      fasebin = ''.join(str(j) for j in fasebinlist)
      faseint = int(fasebin,2)
      phase = faseint / (2. ** (len(ancillas)))
      results = np.append(results,phase)
      All(Measure) | autovector
      eng.flush()
      
   perc_75 = np.percentile(results,75)
   assert perc_75 == pytest.approx(.65625, abs=1e-2), "Percentile 75 not as expected (%f)" % (perc_75)

def test_X_no_eigenvectors():
   eng = MainEngine()
   results = np.array([])
   results_plus = np.array([])
   results_minus = np.array([])
   for i in range(100):
      autovector = eng.allocate_qureg(1)
      amplitude0 = (np.sqrt(2) + np.sqrt(6))/4.
      amplitude1 = (np.sqrt(2) - np.sqrt(6))/4.
      StatePreparation([amplitude0, amplitude1]) | autovector
      unit = X
      ancillas = eng.allocate_qureg(1)
      pe.PhaseEstimation(unit) | (ancillas,autovector)
      get_inverse(QFT) | ancillas
      All(Measure) | ancillas
      fasebinlist = [int(q) for q in ancillas]
      fasebin = ''.join(str(j) for j in fasebinlist)
      faseint = int(fasebin,2)
      phase = faseint / (2. ** (len(ancillas)))
      results = np.append(results,phase)
      Tensor(H) | autovector
      if np.allclose(phase,.0,rtol=1e-1):
         results_plus = np.append(results_plus,phase)
         All(Measure) | autovector
         autovector_result = int(autovector)
         assert autovector_result == 0
      elif np.allclose(phase,.5,rtol=1e-1):
         results_minus = np.append(results_minus,phase)
         All(Measure) | autovector
         autovector_result = int(autovector)
         assert autovector_result == 1
      else:
         All(Measure) | autovector
      eng.flush()

   total = len(results_plus) + len(results_minus)
   ratio = float(len(results_plus))/float(len(results_minus))
   assert total == pytest.approx(100,abs=5)
   assert ratio == pytest.approx(1./3., abs = 1e-1), "Statistical ratio is not correct (%f %d %d)" % (ratio,len(results_plus),len(results_minus))


def test_n_qureg():
   eng = MainEngine()
   autovector = eng.allocate_qureg(1)
   ancillas = eng.allocate_qureg(1)
   unit = X
   with pytest.raises(TypeError):
      pe.PhaseEstimation(unit) | (ancillas,autovector,autovector)
   with pytest.raises(TypeError):
      pe.PhaseEstimation(unit) | ancillas
