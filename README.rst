=========
SINGAL(1)
=========

NAME
====

**singal** — keep a remote directory up-to-date with local changes.

SYNOPSIS
========

| **singal** **SOURCE** **TARGET**

DESCRIPTION
===========

After an initial call to **rsync** to bring **TARGET** up-to-date with
**SOURCE**, **singal** monitors **SOURCE**, transfering files as soon as they
are created, modified, or deleted.

An *.singalignore* file containing rsync exclude patterns is required in
**SOURCE**. It is used to exclude files from monitoring and transfer. It is
passed as an argument to the **rsync** **--exclude-from** option.

The *.singalignore* file is also used to generate **fswatch** exclusion rules.
To support this, **singal** must convert the patterns into regular
expressions suitable for passing to the **fswatch** **--exclude** option. Two
features of rsync patterns are not supported:

1. Character classes: if **singal** encounters a character class, it will exit
   with an error message.

2. Directory-only rules: if **singal** encounters a directory only rule (that
   is, one that ends with “/” or “/***”), it will proceed with a warning that
   the resulting pattern will match any type, not just directories. (This is an
   **fswatch** limitation.)

OPTIONS
=======

SOURCE
   Path to source directory. Must be a local path.

TARGET
   Path to destination directory. Must be specified using rsync syntax. May be
   remote.

FILES
=====

*.singalignore*
   List of patterns to exclude from monitoring and transfer, in rsync

BUGS
====

This program has no unit tests.

There are surely unforseen corner cases.

SEE ALSO
========

**rsync(1)**, **fswatch(1)**
