=====================
FSWATCH-RSYNC-SEND(1)
=====================

NAME
====

**fswatch-rsync-send** — keep a remote mirror up-to-date with local changes.

SYNOPSIS
========

| **fswatch-rsync-send** **SOURCE** **TARGET**

DESCRIPTION
===========

After an initial call to **rsync** to bring **TARGET** up-to-date with
**SOURCE**, **fswatch-rsync-send** monitors **SOURCE**, transfering files as
soon as they are created, modified, or deleted.

An *.rsync-exclude* file is required in **SOURCE**. It is used to exclude files
from monitoring and transfer. It is passed as an argument to the **rsync**
**--exclude-from** option for the initial sync.

The *.rsync-exclude* file is also used to generate **fswatch** exclusion rules.
To support this, **fswatch-rsync-send** must convert the patterns into regular
expressions suitable for passing to the **fswatch** **--exclude** option. Two
features of rsync patterns are not supported:

1. Character classes: if **fswatch-rsync-send** encounters a character class, it
   will exit with an error message.

2. Directory-only rules: if **fswatch-rsync-send** encounters a directory only
   rule (that is, one that ends with “/” or “/***”), it will proceed with a
   warning that the resulting pattern will match any type, not just directories.
   (This is an **fswatch** limitation.)

OPTIONS
=======

SOURCE
   Path to source directory. Must be a local path.

TARGET
   Path to destination directory. Must be specified using rsync syntax. May be
   remote.

FILES
=====

*.rsync-exclude*
   List of patterns to exclude from monitoring and transfer.

BUGS
====

This program has no unit tests.

There are no doubt corner cases that I haven't considered.

SEE ALSO
========

**rsync(1)**, **fswatch(1)**
