import collections
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

from readline0 import readline0

fswatch_args = [
    '--recursive',
    '--extended',
    #'--no-defer',
    '--batch-marker',
    '--print0',
]

rsync_args = [
    '--rsh', shlex.join(['ssh', '-o', 'ControlMaster=auto',
                                '-o', 'ControlPath=~/.ssh/control/%C',
                                '-o', 'ControlPersist=yes']),
    '--links',
    '--executability', #'--perms',
    '--times',
    #'--group',
    #'--owner',
    #'--devices',
    #'--specials',
    #'--acls',
    #'--xattrs',
    #'--atimes',
    #'--crtimes',
    #'--hard-links',
    '--relative',
    '--itemize-changes',
    '--debug=FILTER',
    #'--dry-run',
]

rsync_initial_args = [
    '--recursive',
    '--delete-delay',
    #'--no-inc-recursive',
    '--info=stats',
    #'--dry-run',
]    

rsync_incremental_args = [
    '--dirs',
    '--delete-missing-args',
    #'--dry-run',
]

trace = False


_re_escape_most_map = {i: '\\'+chr(i) for i in b'()[]{}?*+|^$\\.\t\n\r\v\f'}
def re_escape_most(pattern):
    """
    Same as re.escape, except that it doesn't escape '-', '&', and '~', which
    are only special in character sets (and make fswatch choke _outside_ of
    character sets) and '#' and ' ', which are only special in verbose mode.
    
    We also assume that our input is a str instead of doing a dubious decode
    from latin1 if it's not.
    
    See CPython’s Lib/re/__init__.py.
    """
    return pattern.translate(_re_escape_most_map)


_re_escape_some_map = {i: '\\'+chr(i) for i in b'()[]{}+|^$\\.\t\n\r\v\f'}
def re_escape_some(pattern):
    """
    Same as re_escape_most, except we don't escape '?' and '*' either.
    """
    return pattern.translate(_re_escape_some_map)


def rsync_pattern_to_fswatch_regex(pat, base):
    '''
    Convert an rsync filter pattern into a regular expression suitable as an
    argument to fswatch’s --exclude option.
    
    Note that this is a _very_ stupid function that only knows how to deal with
    a small subset of the rsync pattern matching grammar. It _should_ complain
    if it runs into syntax it doesn’t recognize, but no guarantees that it's not
    going to cock things up royally.
    '''
    orig_pat = pat
    regex_base = '^' + re_escape_most(str(base.absolute()))
    
    # Things that can happen at the beginning of a pattern
    
    if pat.startswith('/'):
        regex_head = '/'
        pat = pat[1:]
    elif pat.startswith('**'):
        regex_head = '/.*'
        pat = pat[2:]
    elif pat.startswith('*'):
        regex_head = '/[^/]*'
        pat = pat[1:]
    else:
        regex_head = '/(.*/)?'
    
    # Things that can happen at the end of a pattern
    
    if pat.endswith('***'):
        regex_tail = '(/.*)?$'
        pat = pat[:-3]
    else:
        regex_tail = '$'
    
    if pat.endswith('/'):
        print(f'warning: partially supported filter pattern “{orig_pat}”:',
              'fswatch does not support filters that match only directories.',
              'This filter will match regardless of type.', file=sys.stderr)
        pat = pat[:-1]
    
    # Things that can happen in the middle of a pattern
    
    if '[' in pat:
        print(f'error: unsupported filter pattern “{orig_pat}”:',
              ' I’m too lazy to implement character class conversion.',
              file=sys.stderr)
        sys.exit(1)
    
    regex = re_escape_some(pat).replace('?', '.') \
                                            .replace('*', '[^/]*') \
                                            .replace('**', '.*')
    
    return regex_base + regex_head + pat + regex_tail


def send_initial(local, remote):
    args = ['rsync',
            *rsync_args,
            *rsync_initial_args,
            f'--exclude-from={local}/.rsync-exclude',
            str(local)+'/./',
            remote]
    if trace:
        print('+', shlex.join(args), file=sys.stderr)
    subprocess.run(args, check=True)


def watch_dir(path, exclusions):
    args = ['fswatch', *fswatch_args]
    args += [f'--exclude={regex}' for regex in exclusions]
    args.append(str(path))
    if trace:
        print('+', shlex.join(args), file=sys.stderr)
    return subprocess.Popen(args, stdout=subprocess.PIPE)


def send_batch(batch, local, remote):
    args = ['rsync',
            *rsync_args,
            *rsync_incremental_args,
            f'--exclude-from={local}/.rsync-exclude',
            *[f'{local}/./{path.relative_to(local)}' for path in batch],
            remote]
    if trace:
        print('+', shlex.join(args), file=sys.stderr)
    proc = subprocess.run(args)
    if proc.returncode in [24]:
        pass
    else:
        proc.check_returncode()


def main():
    global fswatch_args
    global rsync_args
    global trace
    
    local = Path(sys.argv[1])
    remote = sys.argv[2]
    
    if fswatch_extra := os.environ.get('FSWATCH_RSYNC_SEND_EXTRA_FSWATCH_ARGS'):
        fswatch_args += shlex.split(fswatch_extra)
    
    if rsync_extra := os.environ.get('FSWATCH_RSYNC_SEND_EXTRA_RSYNC_ARGS'):
        rsync_args += shlex.split(rsync_extra)
    
    if trace_var := os.environ.get('FSWATCH_RSYNC_SEND_TRACE'):
        trace = bool(trace_var)
    
    with open(local/'.rsync-exclude') as rsync_exclusions:
        exclusions = [rsync_pattern_to_fswatch_regex(line.rstrip('\n'), local)
                      for line in rsync_exclusions]
    
    send_initial(local, remote)
    proc = watch_dir(local, exclusions)
    batch = []
    for line in readline0(proc.stdout, separator=b'\x00', blocksize=1):
        line = line.decode()
        if line == 'NoOp':
            send_batch(batch, local.absolute(), remote)
            batch.clear()
        else:
            path = Path(line)
            if trace:
                print(f'fswatch: “{path}”', file=sys.stderr)
            batch.append(path)
