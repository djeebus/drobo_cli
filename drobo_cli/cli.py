import click
import enum
import prettytable

from drobo_cli.command import CommandClient
from drobo_cli.status import StatusClient


@click.group()
@click.argument('host')
@click.pass_context
def cli(ctx, host):
    ctx.obj = {
        'host': host,
    }


def parse_status(number):
    number = number.pyval

    is_full = (number & 0x10000 == 0x10000)
    number &= ~0x10000

    return to_enum(number, DroboStatus), is_full


@cli.command()
@click.pass_context
def status(ctx):
    client = StatusClient(ctx.obj['host'])
    msg = client.get_status()

    total_cap_protected = to_size(msg.mTotalCapacityProtected)
    used_cap_protected = to_size(msg.mUsedCapacityProtected)

    overall, is_full = parse_status(msg.mStatus)
    print(f'status: {overall.name}')
    print(f'is full: {is_full}')
    print(f'ESA ID: {msg.mESAID.pyval}')
    print(f'has apps: {msg.DroboApps.DNASDroboAppsEnabled.pyval == 1}')
    print(f'disk pack status: {msg.mDiskPackStatus.pyval}')
    print(f'drobo model: {msg.mModel.pyval}')
    print(f'drobo name: {msg.mDroboName.pyval}')
    print(f'drobo version: {msg.mVersion.pyval}')
    print(f'protected capacity: {used_cap_protected}/{total_cap_protected}')

    table = prettytable.PrettyTable(
        ['#', 'Status', 'Errors', 'Type', 'Make', 'Firmware', 'Serial', 'Size'],
    )

    for index in range(msg.mSlotCountExp.pyval):
        disk_info = getattr(msg.mSlotsExp, f'n{index}')
        disk_type = to_enum(disk_info.mDiskType, DiskType)

        table.add_row([
            index+1,
            to_enum(disk_info.mStatus, DiskStatus).name,
            disk_info.mErrorCount.pyval,
            disk_type.name,
            disk_info.mMake,
            disk_info.mDiskFwRev,
            disk_info.mSerial,
            to_size(disk_info.mPhysicalCapacity),
        ])

    print(table)


@cli.command()
@click.pass_context
def shares(ctx):
    host = ctx.obj['host']

    status_client = StatusClient(host)
    status = status_client.get_status()
    esa_id = status.mESAID.pyval

    command_client = CommandClient(host, esa_id)
    response = command_client.get_share_config()

    table = prettytable.PrettyTable(
        [
            'Name',
            'TimeMachine',
        ],
    )

    shares = response.xpath('/TMCmd/ResultDetails/DRINASConfig/DRIShareConfig/Shares/Share')
    for share in shares:
        table.add_row([
            share.find('ShareName').text,
            share.find('TimeMachineEnabled').text == '1',
        ])

    print(table)


@cli.command()
@click.pass_context
def network(ctx):
    host = ctx.obj['host']

    status_client = StatusClient(host)
    status = status_client.get_status()
    esa_id = status.mESAID.pyval

    command_client = CommandClient(host, esa_id)
    response = command_client.get_network_config()

    config = response.xpath('/TMCmd/ResultDetails/DRINASConfig/DRINasNetworkConfig')[0]
    ip_config = config.find('IPConfig')
    jumbo_frames = config.find('JumboFramesConfig')
    jumbo_frames_flag = jumbo_frames.find('Enabled').text == "1"
    mtu_size = jumbo_frames.find('MTUSize').text
    print(f"""
Name: {config.find('NasName').text}
Workgroup: {config.find('NasWorkgroup').text}
MAC Address: {config.find('MACAddress').text}
Port Speed: {config.find('PortSpeed').text} Mbps
Port Duplex: {config.find('PortDuplex').text}

Type: {"Static" if ip_config.find('IPConfigType').text == '1' else "DHCP"}
IP Address: {ip_config.find('IP').text}
Subnet: {ip_config.find('Subnet').text}
Gateway: {ip_config.find('Gateway').text}
DNS1: {ip_config.find('DNS1').text}
DNS2: {ip_config.find('DNS2').text}

Jumbo Frames: {"Enabled" if jumbo_frames_flag else "Disabled"}
MTU Size: {mtu_size}
""".strip())


def to_enum(value, enum_cls):
    if not isinstance(value, int):
        value = value.pyval
    return enum_cls(value)


class DroboStatus(enum.Enum):
    OK = 0x8000
    Yellow = 0x8004
    Red = 0x8006
    BadDrive = 0x8010
    DriveRemoved = 0x8046
    Unknown = 0x8052
    DataProtectionInProgress = 0x8240
    DataProtectionInProgress2 = 0x8244


class DiskStatus(enum.Enum):
    FullRed = 0x01
    FullYellow = 0x02
    Green = 0x03
    DataProtection = 0x04
    Empty = 0x80
    Removed = 0x81
    Failure = 0x86


class DiskType(enum.Enum):
    HDD = 0
    mSataSSD = 4


suffixes = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}


def to_size(size):
    if size == 0:
        return ''

    size = size.pyval

    power = 1000
    n = 0
    while size > power:
        size /= power
        n += 1

    size = int(size)
    return f'{size} {suffixes[n]}B'


if __name__ == '__main__':
    cli()
