from projectq.ops import CNOT, H, RelativeCommand, _basics


def test_relative_command_equals():
    cmd1 = RelativeCommand(H, 0)
    cmd2 = RelativeCommand(H, 0)
    cmd3 = RelativeCommand(H, 1)
    cmd4 = RelativeCommand(CNOT, 0, 1)
    cmd5 = RelativeCommand(CNOT, 0, 1)
    cmd6 = RelativeCommand(CNOT, 1, 0)
    cmd7 = RelativeCommand(CNOT, 0, 2)
    cmd8 = RelativeCommand(CNOT, 2, 1)
    assert cmd1 == cmd2
    assert cmd1 != cmd3
    assert cmd4 == cmd5
    assert cmd4 != cmd6
    assert cmd4 != cmd7
    assert cmd4 != cmd8
