# Copyright 2015 ClusterHQ. See LICENSE file for details.

"""
Helper routines for converting ``errno`` style error codes from C functions
to Python exceptions defined by `libzfs_core` API.

The conversion heavily depends on the context of the error: the attempted
operation and the input parameters.  For this reason, there is a conversion
routine for each `libzfs_core` interface function. The conversion routines
have the return code as a parameter as well as all the parameters of the
corresponding interface functions.

The parameters and exceptions are documented in the `libzfs_core` interfaces.
"""

import errno
import os
import re
import string
from . import exceptions as lzc_exc
from ._constants import MAXNAMELEN


def lzc_create_xlate_error(ret, name, is_zvol, props):
    if ret == 0:
        return
    if ret == errno.EINVAL:
        if not _is_valid_fs_name(name):
            raise lzc_exc.NameInvalid(name)
        elif len(name) > MAXNAMELEN:
            raise lzc_exc.NameTooLong(name)
        else:
            raise lzc_exc.PropertyInvalid(name)

    if ret == errno.EEXIST:
        raise lzc_exc.FilesystemExists(name)
    if ret == errno.ENOENT:
        raise lzc_exc.ParentNotFound(name)
    raise _generic_exception(ret, name, "Failed to create filesystem")


def lzc_clone_xlate_error(ret, name, origin, props):
    if ret == 0:
        return
    if ret == errno.EINVAL:
        if not _is_valid_fs_name(name):
            raise lzc_exc.FilesystemNameInvalid(name)
        elif not _is_valid_snap_name(origin):
            raise lzc_exc.SnapshotNameInvalid(origin)
        elif len(name) > MAXNAMELEN:
            raise lzc_exc.NameTooLong(name)
        elif len(origin) > MAXNAMELEN:
            raise lzc_exc.NameTooLong(origin)
        elif _pool_name(name) != _pool_name(origin):
            raise lzc_exc.PoolsDiffer(name) # see https://www.illumos.org/issues/5824
        else:
            raise lzc_exc.PropertyInvalid(name)

    if ret == errno.EEXIST:
        raise lzc_exc.FilesystemExists(name)
    if ret == errno.ENOENT:
        if not _is_valid_snap_name(origin):
            raise lzc_exc.SnapshotNameInvalid(origin)
        raise lzc_exc.DatasetNotFound(name)
    raise _generic_exception(ret, name, "Failed to create clone")


def lzc_rollback_xlate_error(ret, name):
    if ret == 0:
        return
    if ret == errno.EINVAL:
        if not _is_valid_fs_name(name):
            raise lzc_exc.NameInvalid(name)
        elif len(name) > MAXNAMELEN:
            raise lzc_exc.NameTooLong(name)
        else:
            raise lzc_exc.SnapshotNotFound(name)
    if ret == errno.ENOENT:
        if not _is_valid_fs_name(name):
            raise lzc_exc.NameInvalid(name)
        else:
            raise lzc_exc.FilesystemNotFound(name)
    raise _generic_exception(ret, name, "Failed to rollback")


def lzc_snapshot_xlate_errors(ret, errlist, snaps, props):
    if ret == 0:
        return

    def _map(ret, name):
        if ret == errno.EXDEV:
            pool_names = map(_pool_name, snaps)
            same_pool = all(x == pool_names[0] for x in pool_names)
            if same_pool:
                return lzc_exc.DuplicateSnapshots(name)
            else:
                return lzc_exc.PoolsDiffer(name)
        elif ret == errno.EINVAL:
            if any(not _is_valid_snap_name(s) for s in snaps):
                return lzc_exc.NameInvalid(name)
            elif any(len(s) > MAXNAMELEN for s in snaps):
                return lzc_exc.NameTooLong(name)
            else:
                return lzc_exc.PropertyInvalid(name)

        if ret == errno.EEXIST:
            return lzc_exc.SnapshotExists(name)
        if ret == errno.ENOENT:
            return lzc_exc.FilesystemNotFound(name)
        return _generic_exception(ret, name, "Failed to create snapshot")

    _handle_err_list(ret, errlist, snaps, lzc_exc.SnapshotFailure, _map)


def lzc_destroy_snaps_xlate_errors(ret, errlist, snaps, defer):
    if ret == 0:
        return

    def _map(ret, name):
        if ret == errno.EEXIST:
            return lzc_exc.SnapshotIsCloned(name)
        if ret == errno.ENOENT:
            return lzc_exc.PoolNotFound(name)
        if ret == errno.EBUSY:
            return lzc_exc.SnapshotIsHeld(name)
        return _generic_exception(ret, name, "Failed to destroy snapshot")

    _handle_err_list(ret, errlist, snaps, lzc_exc.SnapshotDestructionFailure, _map)


def lzc_bookmark_xlate_errors(ret, errlist, bookmarks):
    if ret == 0:
        return

    def _map(ret, name):
        if ret == errno.EINVAL:
            if name:
                snap = bookmarks[name]
                pool_names = map(_pool_name, bookmarks.keys())
                if not _is_valid_bmark_name(name):
                    return lzc_exc.BookmarkNameInvalid(name)
                elif not _is_valid_snap_name(snap):
                    return lzc_exc.SnapshotNameInvalid(snap)
                elif _fs_name(name) != _fs_name(snap):
                    return lzc_exc.BookmarkMismatch(name)
                elif any(x != _pool_name(name) for x in pool_names):
                    return lzc_exc.PoolsDiffer(name)
            else:
                invalid_names = [b for b in bookmarks.keys() if not _is_valid_bmark_name(b)]
                if invalid_names:
                    return lzc_exc.BookmarkNameInvalid(invalid_names[0])
        if ret == errno.EEXIST:
            return lzc_exc.BookmarkExists(name)
        if ret == errno.ENOENT:
            return lzc_exc.SnapshotNotFound(name)
        if ret == errno.ENOTSUP:
            return lzc_exc.BookmarkNotSupported(name)
        return _generic_exception(ret, name, "Failed to create bookmark")

    _handle_err_list(ret, errlist, bookmarks.keys(), lzc_exc.BookmarkFailure, _map)


def lzc_get_bookmarks_xlate_error(ret, fsname, props):
    if ret == 0:
        return
    if ret == errno.ENOENT:
        raise lzc_exc.FilesystemNotFound(fsname)
    raise _generic_exception(ret, fsname, "Failed to list bookmarks")


def lzc_destroy_bookmarks_xlate_errors(ret, errlist, bookmarks):
    if ret == 0:
        return

    def _map(ret, name):
        if ret == errno.EINVAL:
            return lzc_exc.NameInvalid(name)
        return _generic_exception(ret, name, "Failed to destroy bookmark")

    _handle_err_list(ret, errlist, bookmarks, lzc_exc.BookmarkDestructionFailure, _map)


def lzc_snaprange_space_xlate_error(ret, firstsnap, lastsnap):
    if ret == 0:
        return
    if ret == errno.EINVAL:
        if not _is_valid_snap_name(firstsnap):
            raise lzc_exc.NameInvalid(firstsnap)
        elif not _is_valid_snap_name(lastsnap):
            raise lzc_exc.NameInvalid(lastsnap)
        elif len(firstsnap) > MAXNAMELEN:
            raise lzc_exc.NameTooLong(firstsnap)
        elif len(lastsnap) > MAXNAMELEN:
            raise lzc_exc.NameTooLong(lastsnap)
        elif _pool_name(firstsnap) != _pool_name(lastsnap):
            raise lzc_exc.PoolsDiffer(lastsnap)
        else:
            raise lzc_exc.SnapshotMismatch(lastsnap)
    if ret == errno.ENOENT:
        raise lzc_exc.SnapshotNotFound(lastsnap)
    raise _generic_exception(ret, lastsnap, "Failed to calculate space used by range of snapshots")


def lzc_hold_xlate_errors(ret, errlist, holds, fd):
    if ret == 0:
        return

    def _map(ret, name):
        if ret == errno.EXDEV:
            return lzc_exc.PoolsDiffer(name)
        elif ret == errno.EINVAL:
            if name:
                tag = holds[name]
                pool_names = map(_pool_name, holds.keys())
                if not _is_valid_snap_name(name):
                    return lzc_exc.NameInvalid(name)
                elif len(name) > MAXNAMELEN:
                    return lzc_exc.NameTooLong(name)
                elif any(x != _pool_name(name) for x in pool_names):
                    return lzc_exc.PoolsDiffer(name)
            else:
                invalid_names = [b for b in holds.keys() if not _is_valid_snap_name(b)]
                if invalid_names:
                    return lzc_exc.NameInvalid(invalid_names[0])
        fs_name = None
        hold_name = None
        pool_name = None
        if name is not None:
            fs_name = _fs_name(name)
            pool_name = _pool_name(name)
            hold_name = holds[name]
        if ret == errno.ENOENT:
            return lzc_exc.FilesystemNotFound(fs_name)
        if ret == errno.EEXIST:
            return lzc_exc.HoldExists(name)
        if ret == errno.E2BIG:
            return lzc_exc.NameTooLong(hold_name)
        if ret == errno.ENOTSUP:
            return lzc_exc.FeatureNotSupported(pool_name)
        return _generic_exception(ret, name, "Failed to hold snapshot")

    if ret == errno.EBADF:
        raise lzc_exc.BadHoldCleanupFD()
    _handle_err_list(ret, errlist, holds.keys(), lzc_exc.HoldFailure, _map)


def lzc_release_xlate_errors(ret, errlist, holds):
    if ret == 0:
        return
    for _, hold_list in holds.iteritems():
        if not isinstance(hold_list, list):
            raise lzc_exc.TypeError('holds must be in a list')

    def _map(ret, name):
        if ret == errno.EXDEV:
            return lzc_exc.PoolsDiffer(name)
        elif ret == errno.EINVAL:
            if name:
                pool_names = map(_pool_name, holds.keys())
                if not _is_valid_snap_name(name):
                    return lzc_exc.NameInvalid(name)
                elif len(name) > MAXNAMELEN:
                    return lzc_exc.NameTooLong(name)
                elif any(x != _pool_name(name) for x in pool_names):
                    return lzc_exc.PoolsDiffer(name)
            else:
                invalid_names = [b for b in holds.keys() if not _is_valid_snap_name(b)]
                if invalid_names:
                    return lzc_exc.NameInvalid(invalid_names[0])
        elif ret == errno.ENOENT:
            return lzc_exc.HoldNotFound(name)
        elif ret == errno.E2BIG:
            tag_list = holds[name]
            too_long_tags = [t for t in tag_list if len(t) > MAXNAMELEN]
            return lzc_exc.NameTooLong(too_long_tags[0])
        elif ret == errno.ENOTSUP:
            pool_name = None
            if name is not None:
                pool_name = _pool_name(name)
            return lzc_exc.FeatureNotSupported(pool_name)
        else:
            return _generic_exception(ret, name, "Failed to release snapshot hold")

    _handle_err_list(ret, errlist, holds.keys(), lzc_exc.HoldReleaseFailure, _map)


def lzc_get_holds_xlate_error(ret, snapname):
    if ret == 0:
        return
    if ret == errno.EINVAL:
        if not _is_valid_snap_name(snapname):
            raise lzc_exc.NameInvalid(snapname)
        elif len(snapname) > MAXNAMELEN:
            raise lzc_exc.NameTooLong(snapname)
    if ret == errno.ENOENT:
        raise lzc_exc.SnapshotNotFound(snapname)
    if ret == errno.ENOTSUP:
        raise lzc_exc.FeatureNotSupported(_pool_name(snapname))
    raise _generic_exception(ret, snapname, "Failed to get holds on snapshot")


def lzc_send_xlate_error(ret, snapname, fromsnap, fd, flags):
    if ret == 0:
        return
    if ret == errno.EXDEV and fromsnap is not None:
        if _pool_name(fromsnap) != _pool_name(snapname):
            raise lzc_exc.PoolsDiffer(snapname)
        else:
            raise lzc_exc.SnapshotMismatch(snapname)
    elif ret == errno.EINVAL:
        if (fromsnap is not None and not _is_valid_snap_name(fromsnap) and
            not _is_valid_bmark_name(fromsnap)):
            raise lzc_exc.NameInvalid(fromsnap)
        elif not _is_valid_snap_name(snapname) and not _is_valid_fs_name(snapname):
            raise lzc_exc.NameInvalid(snapname)
        elif fromsnap is not None and len(fromsnap) > MAXNAMELEN:
            raise lzc_exc.NameTooLong(fromsnap)
        elif len(snapname) > MAXNAMELEN:
            raise lzc_exc.NameTooLong(snapname)
        elif fromsnap is not None and _pool_name(fromsnap) != _pool_name(snapname):
            raise lzc_exc.PoolsDiffer(snapname)
    elif ret == errno.ENOENT:
        if (fromsnap is not None and not _is_valid_snap_name(fromsnap) and
            not _is_valid_bmark_name(fromsnap)):
            raise lzc_exc.NameInvalid(fromsnap)
        raise lzc_exc.SnapshotNotFound(snapname)
    elif ret == errno.ENAMETOOLONG:
        if fromsnap is not None and len(fromsnap) > MAXNAMELEN:
            raise lzc_exc.NameTooLong(fromsnap)
        else:
            raise lzc_exc.NameTooLong(snapname)
    raise lzc_exc.StreamIOError(ret)


def lzc_send_space_xlate_error(ret, snapname, fromsnap):
    if ret == 0:
        return
    if ret == errno.EXDEV and fromsnap is not None:
        if _pool_name(fromsnap) != _pool_name(snapname):
            raise lzc_exc.PoolsDiffer(snapname)
        else:
            raise lzc_exc.SnapshotMismatch(snapname)
    elif ret == errno.EINVAL:
        if fromsnap is not None and not _is_valid_snap_name(fromsnap):
            raise lzc_exc.NameInvalid(fromsnap)
        elif not _is_valid_snap_name(snapname):
            raise lzc_exc.NameInvalid(snapname)
        elif fromsnap is not None and len(fromsnap) > MAXNAMELEN:
            raise lzc_exc.NameTooLong(fromsnap)
        elif len(snapname) > MAXNAMELEN:
            raise lzc_exc.NameTooLong(snapname)
        elif fromsnap is not None and _pool_name(fromsnap) != _pool_name(snapname):
            raise lzc_exc.PoolsDiffer(snapname)
    elif ret == errno.ENOENT and fromsnap is not None:
        if not _is_valid_snap_name(fromsnap):
            raise lzc_exc.NameInvalid(fromsnap)
    if ret == errno.ENOENT:
        raise lzc_exc.SnapshotNotFound(snapname)
    raise _generic_exception(ret, snapname, "Failed to estimate backup stream size")


def lzc_receive_xlate_error(ret, snapname, fd, force, origin, props):
    if ret == 0:
        return
    if ret == errno.EINVAL:
        if not _is_valid_snap_name(snapname):
            raise lzc_exc.NameInvalid(snapname)
        elif len(snapname) > MAXNAMELEN:
            raise lzc_exc.NameTooLong(snapname)
        elif origin is not None and not _is_valid_snap_name(origin):
            raise lzc_exc.NameInvalid(origin)
        else:
            raise lzc_exc.BadStream()
    if ret == errno.ENOENT:
        if not _is_valid_snap_name(snapname):
            raise lzc_exc.NameInvalid(snapname)
        else:
            raise lzc_exc.DatasetNotFound(snapname)
    if ret == errno.EEXIST:
        raise lzc_exc.DatasetExists(snapname)
    if ret == errno.ENOTSUP:
        raise lzc_exc.StreamFeatureNotSupported()
    if ret == errno.ENODEV:
        raise lzc_exc.StreamMismatch(_fs_name(snapname))
    if ret == errno.ETXTBSY:
        raise lzc_exc.DestinationModified(_fs_name(snapname))
    if ret == errno.EBUSY:
        raise lzc_exc.DatasetBusy(_fs_name(snapname))
    if ret == errno.ENOSPC:
        raise lzc_exc.NoSpace(_fs_name(snapname))
    if ret == errno.EDQUOT:
        raise lzc_exc.QuotaExceeded(_fs_name(snapname))
    if ret == errno.ENAMETOOLONG:
        raise lzc_exc.NameTooLong(snapname)
    if ret == errno.EROFS:
        raise lzc_exc.ReadOnlyPool(_pool_name(snapname))
    if ret == errno.EAGAIN:
        raise lzc_exc.SuspendedPool(_pool_name(snapname))

    raise lzc_exc.StreamIOError(ret)


def _handle_err_list(ret, errlist, names, exception, mapper):
    '''
    Convert one or more errors from an operation into the requested exception.

    :param int ret: the overall return code.
    :param errlist: the dictionary that maps entity names to their specific error codes.
    :type errlist: dict of bytes:int
    :param names: the list of all names of the entities on which the operation was attempted.
    :param type exception: the type of the exception to raise if an error occurred.
                           The exception should be a subclass of `MultipleOperationsFailure`.
    :param function mapper: the function that maps an error code and a name to a Python exception.

    Unless ``ret`` is zero this function will raise the ``exception``.
    If the ``errlist`` is not empty, then the compound exception will contain a list of exceptions
    corresponding to each individual error code in the ``errlist``.
    Otherwise, the ``exception`` will contain a list with a single exception corresponding to the
    ``ret`` value.  If the ``names`` list contains only one element, that is, the operation was
    attempted on a single entity, then the name of that entity is passed to the ``mapper``.
    If the operation was attempted on multiple entities, but the ``errlist`` is empty, then we
    can not know which entity caused the error and, thus, ``None`` is used as a name to signify
    thati fact.

    .. note::
        Note that the ``errlist`` can contain a special element with a key of "N_MORE_ERRORS".
        That element means that there were too many errors to place on the ``errlist``.
        Those errors are suppressed and only their count is provided as a value of the special
        ``N_MORE_ERRORS`` element.
    '''
    if ret == 0:
        return

    if len(errlist) == 0:
        suppressed_count = 0
        if len(names) == 1:
            name = names[0]
        else:
            name = None
        errors = [mapper(ret, name)]
    else:
        errors = []
        suppressed_count = errlist.pop('N_MORE_ERRORS', 0)
        for name, err in errlist.iteritems():
            errors.append(mapper(err, name))

    raise exception(errors, suppressed_count)


def _pool_name(name):
    '''
    Extract a pool name from the given dataset or bookmark name.

    '/' separates dataset name components.
    '@' separates a snapshot name from the rest of the dataset name.
    '#' separates a bookmark name from the rest of the dataset name.
    '''
    return re.split('[/@#]', name, 1)[0]


def _fs_name(name):
    '''
    Extract a dataset name from the given snapshot or bookmark name.

    '@' separates a snapshot name from the rest of the dataset name.
    '#' separates a bookmark name from the rest of the dataset name.
    '''
    return re.split('[@#]', name, 1)[0]


def _is_valid_name_component(component):
    allowed = string.ascii_letters + string.digits + '-_.: '
    return component and all(x in allowed for x in component)


def _is_valid_fs_name(name):
    return name and all(_is_valid_name_component(c) for c in name.split('/'))


def _is_valid_snap_name(name):
    parts = name.split('@')
    return (len(parts) == 2 and _is_valid_fs_name(parts[0]) and
           _is_valid_name_component(parts[1]))


def _is_valid_bmark_name(name):
    parts = name.split('#')
    return (len(parts) == 2 and _is_valid_fs_name(parts[0]) and
           _is_valid_name_component(parts[1]))


def _generic_exception(err, name, message):
    if err in _error_to_exception:
        return _error_to_exception[err](name)
    else:
        return lzc_exc.ZFSGenericError(err, message, name)

_error_to_exception = { e.errno: e for e in [
    lzc_exc.ZIOError,
    lzc_exc.NoSpace,
    lzc_exc.QuotaExceeded,
    lzc_exc.DatasetBusy,
    lzc_exc.NameTooLong,
    lzc_exc.ReadOnlyPool,
    lzc_exc.SuspendedPool,
    lzc_exc.PoolsDiffer,
    lzc_exc.PropertyNotSupported,
]}


# vim: softtabstop=4 tabstop=4 expandtab shiftwidth=4
