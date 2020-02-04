import pytest
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


@pytest.fixture(params=get_available_isometries_decompositions())
def decomposition_module(request):
    replacements = {}
    if request.param == 'python':
        from projectq.libs.isometries.decompose_diagonal import _DecomposeDiagonal
        from projectq.libs.isometries.decompose_ucg import _DecomposeUCG
        from projectq.libs.isometries.decompose_isometry import _DecomposeIsometry

        replacements['_DecomposeDiagonal'] = decompositions._DecomposeDiagonal
        decompositions._DecomposeDiagonal = _DecomposeDiagonal

        replacements['_DecomposeUCG'] = decompositions._DecomposeUCG
        decompositions._DecomposeUCG = _DecomposeUCG

        replacements['_DecomposeIsometry'] = decompositions._DecomposeIsometry
        decompositions._DecomposeIsometry = _DecomposeIsometry
    else:
        from projectq.libs.isometries import cppdec
        from projectq.libs.isometries.decompose_ucg import _DecomposeUCG
        from projectq.libs.isometries.decompose_isometry import _DecomposeIsometry
        assert decompositions._DecomposeDiagonal is cppdec._DecomposeDiagonal
        assert decompositions._DecomposeUCG is not _DecomposeUCG
        assert decompositions._DecomposeIsometry is not _DecomposeIsometry

    yield None

    for func_name, func in replacements.items():
        setattr(decompositions, func_name, func)
