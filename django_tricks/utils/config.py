import os
import string
from configparser import ConfigParser

from django.core.exceptions import ImproperlyConfigured
from django.utils.crypto import get_random_string
from filelock import FileLock


class FilePermissionError(Exception):
    """The key file permissions are insecure."""
    pass


VALID_KEY_CHARS = string.ascii_uppercase + string.ascii_lowercase + string.digits


def load_environment(envname, basedir, key_length=64):
    config = None

    # We don't create a lockfike in the project path, this is
    # necesary for making it work with Vagrant NFS integration
    envdir = os.path.expanduser("~/.environment")

    if not os.path.exists(envdir):
        old_umask = os.umask(0o077)  # Use '0700' file permissions
        os.mkdir(envdir)
        os.umask(old_umask)

    if (os.stat(envdir).st_mode & 0o777) != 0o700:
        raise FilePermissionError("Insecure environment directory permission %s! Make it 700" % envdir)

    envuser = os.path.join(envdir, envname)
    envlocal = os.path.join(basedir, envname)

    envuser_lock = FileLock('%s.lock' % envuser, timeout=1)
    envlocal_lock = FileLock('%s.lock' % envlocal, timeout=1)

    with envuser_lock, envlocal_lock:
        assert envuser_lock.is_locked, "Lock file for the environment file is not available "
        assert envlocal_lock.is_locked, "Lock file for the environment file is not available "

        if not os.path.exists(envuser):
            # Create empty file if it doesn't exists

            old_umask = os.umask(0o177)  # Use '0600' file permissions
            config = ConfigParser()
            config.add_section('django')
            config['django']['secret_key'] = get_random_string(key_length, VALID_KEY_CHARS)

            with open(envuser, 'w') as configfile:
                config.write(configfile)
            os.umask(old_umask)

        if (os.stat(envuser).st_mode & 0o777) != 0o600:
            raise FilePermissionError("Insecure environment file permissions for %s! Make it 600" % envuser)

        if os.path.exists(envlocal):
            if (os.stat(envlocal).st_mode & 0o777) != 0o600:
                raise FilePermissionError("Insecure environment file permissions for %s! Make it 600" % envlocal)

        if not config:
            config = ConfigParser()
            config.read([envuser, envlocal])

        if not config.has_section('django'):
            raise ImproperlyConfigured('Missing `django` section in the environment file.')

        if not config.get('django', 'secret_key', fallback=None):
            raise ImproperlyConfigured('Missing `secret_key` in django section in the environment file.')

        # Register all keys as environment variables
        for key, value in config.items('django'):
            ENVNAME = 'DJANGO_%s' % key.upper()
            if ENVNAME not in os.environ:  # Don't replace existing defined variables
                os.environ[ENVNAME] = value

    assert (not envuser_lock.is_locked)
    assert (not envlocal_lock.is_locked)

    os.unlink('%s.lock' % envuser)
    os.unlink('%s.lock' % envlocal)
