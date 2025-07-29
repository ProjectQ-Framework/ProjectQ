import numpy as np


class PhaseAgnosticStateComparator:
    def __init__(self, tol=1e-8):
        self.tol = tol

    def _validate_state(self, state, label="input"):
        if not isinstance(state, np.ndarray):
            raise TypeError(f"{label} must be a NumPy array.")
        if state.ndim not in (1, 2):
            raise ValueError(f"{label} must be a 1D or 2D array, got shape {state.shape}.")
        if not np.isfinite(state).all():
            raise ValueError(f"{label} contains NaN or Inf.")
        if state.ndim == 1 and np.linalg.norm(state) == 0:
            raise ValueError(f"{label} is a zero vector and cannot be normalized.")
        if state.ndim == 2:
            for i, vec in enumerate(state):
                if np.linalg.norm(vec) == 0:
                    raise ValueError(f"{label}[{i}] is a zero vector.")

    def normalize(self, state, label="input"):
        self._validate_state(state, label)
        if state.ndim == 1:
            return state / np.linalg.norm(state)
        else:
            return np.array([vec / np.linalg.norm(vec) for vec in state])

    def align_phase(self, actual, expected):
        a = self.normalize(actual, "actual")
        b = self.normalize(expected, "expected")
        if a.ndim == 1:
            phase = np.vdot(b, a)
            return actual * phase.conjugate()
        else:
            aligned = []
            for i in range(a.shape[0]):
                phase = np.vdot(b[i], a[i])
                aligned_vec = actual[i] * phase.conjugate()
                aligned.append(aligned_vec)
            return np.array(aligned)

    def compare(self, actual, expected):
        aligned = self.align_phase(actual, expected)
        if actual.ndim == 1:
            if not np.allclose(aligned, expected, atol=self.tol):
                raise AssertionError("States differ beyond tolerance.")
        else:
            for i in range(actual.shape[0]):
                if not np.allclose(aligned[i], expected[i], atol=self.tol):
                    raise AssertionError(f"State {i} differs:\nAligned: {aligned[i]}\nExpected: {expected[i]}")
