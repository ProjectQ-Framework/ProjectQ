import pytest
import projectq
import projectq.libs.isometries.decompositions
import projectq.libs.isometries.decompositions as decompositions


def get_available_isometries_decompositions():
    result = ["python"]
    try:
        from projectq.libs.isometries import cppdec
        result.append("cpp")
    except ImportError:
        # The C++ module was either not installed or is misconfigured. Skip.
        pass
    return result


@pytest.fixture(params=get_available_isometries_decompositions(),
                scope='function')
def iso_decomp_chooser(request, monkeypatch):
    from projectq.libs.isometries.decompose_diagonal import _DecomposeDiagonal
    from projectq.libs.isometries.decompose_ucg import _DecomposeUCG
    from projectq.libs.isometries.decompose_isometry import _DecomposeIsometry

    def _decompose_dg(phases):
        return _DecomposeDiagonal(phases).get_decomposition()

    def _decompose_ucg(gates):
        return _DecomposeUCG(gates).get_decomposition()

    def _decompose_ig(columns, threshold):
        return _DecomposeIsometry(columns, threshold).get_decomposition()

    if request.param == 'python':
        monkeypatch.setattr(projectq.libs.isometries,
                            "_decompose_diagonal_gate",
                            _decompose_dg)
        monkeypatch.setattr(projectq.libs.isometries.decompositions,
                            "_decompose_diagonal_gate",
                            _decompose_dg)

        monkeypatch.setattr(projectq.libs.isometries,
                            "_decompose_uniformly_controlled_gate",
                            _decompose_ucg)
        monkeypatch.setattr(projectq.libs.isometries.decompositions,
                            "_decompose_uniformly_controlled_gate",
                            _decompose_ucg)

        monkeypatch.setattr(projectq.libs.isometries,
                            "_decompose_isometry",
                            _decompose_ig)
        monkeypatch.setattr(projectq.libs.isometries.decompositions,
                            "_decompose_isometry",
                            _decompose_ig)

        assert decompositions._decompose_diagonal_gate is _decompose_dg
        assert decompositions._decompose_uniformly_controlled_gate is _decompose_ucg
        assert decompositions._decompose_isometry is _decompose_ig

    else:
        # Make sure we are not using the Python verison of the important
        # classes
        assert decompositions._DecomposeDiagonal is not _DecomposeDiagonal
        assert decompositions._DecomposeUCG is not _DecomposeUCG
        assert decompositions._DecomposeIsometry is not _DecomposeIsometry
