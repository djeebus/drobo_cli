import unittest.mock


def test_parse_drobo_enum():
    from drobo_cli.cli import parse_status, DroboStatus

    def _(num):
        return unittest.mock.Mock(pyval=num)

    assert parse_status(_(0x8000)) == (DroboStatus.OK, False)
    assert parse_status(_(0x18000)) == (DroboStatus.OK, True)

    assert parse_status(_(0x08006)) == (DroboStatus.Red, False)
    assert parse_status(_(0x18006)) == (DroboStatus.Red, True)
