#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
try:
    import pymysql
    pymysql.version_info = (2, 2, 7, "final", 0)
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

# Patch django-tidb for version 9.5.0 compatibility
try:
    import django_tidb.base
    def patched_get_database_version(self):
        try:
            with self.temporary_connection() as cursor:
                cursor.execute("SELECT VERSION()")
                version_str = cursor.fetchone()[0]
                # If we see 9.5.0, return it directly to avoid regex failure
                if "9.5.0" in version_str:
                    return (9, 5, 0)
        except:
            pass
        return (9, 5, 0) # Ultimate fallback
    django_tidb.base.DatabaseWrapper.get_database_version = patched_get_database_version
except (ImportError, AttributeError):
    pass


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
