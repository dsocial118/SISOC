 Traceback (most recent call last):
   File "/usr/local/lib/python3.11/site-packages/django/template/utils.py", line 69, in __getitem__
     return self._engines[alias]
            ~~~~~~~~~~~~~^^^^^^^
 KeyError: 'django'
 
 During handling of the above exception, another exception occurred:
 
 Traceback (most recent call last):
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 128, in get_package_libraries
     module = import_module(entry[1])
              ^^^^^^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/importlib/__init__.py", line 126, in import_module
     return _bootstrap._gcd_import(name[level:], package, level)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   File "<frozen importlib._bootstrap>", line 1204, in _gcd_import
   File "<frozen importlib._bootstrap>", line 1176, in _find_and_load
   File "<frozen importlib._bootstrap>", line 1147, in _find_and_load_unlocked
   File "<frozen importlib._bootstrap>", line 690, in _load_unlocked
   File "<frozen importlib._bootstrap_external>", line 940, in exec_module
   File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed
   File "/sisoc/core/templatetags/custom_filters.py", line 6, in <module>
     from django.template.base import Undefined
 ImportError: cannot import name 'Undefined' from 'django.template.base' (/usr/local/lib/python3.11/site-packages/django/template/base.py)
 
 The above exception was the direct cause of the following exception:
 
 Traceback (most recent call last):
   File "/sisoc/manage.py", line 38, in <module>
     main()
   File "/sisoc/manage.py", line 34, in main
     execute_from_command_line(sys.argv)
   File "/usr/local/lib/python3.11/site-packages/django/core/management/__init__.py", line 442, in execute_from_command_line
     utility.execute()
   File "/usr/local/lib/python3.11/site-packages/django/core/management/__init__.py", line 436, in execute
     self.fetch_command(subcommand).run_from_argv(self.argv)
   File "/usr/local/lib/python3.11/site-packages/django/core/management/base.py", line 412, in run_from_argv
     self.execute(*args, **cmd_options)
   File "/usr/local/lib/python3.11/site-packages/django/core/management/base.py", line 453, in execute
     self.check()
   File "/usr/local/lib/python3.11/site-packages/django/core/management/base.py", line 485, in check
     all_issues = checks.run_checks(
                  ^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/core/checks/registry.py", line 88, in run_checks
     new_errors = check(app_configs=app_configs, databases=databases)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/contrib/admin/checks.py", line 78, in check_dependencies
     for engine in engines.all():
                   ^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/template/utils.py", line 94, in all
     return [self[alias] for alias in self]
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/template/utils.py", line 94, in <listcomp>
     return [self[alias] for alias in self]
             ~~~~^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/template/utils.py", line 85, in __getitem__
     engine = engine_cls(params)
              ^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 24, in __init__
     options["libraries"] = self.get_templatetag_libraries(libraries)
                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 42, in get_templatetag_libraries
     libraries = get_installed_libraries()
                 ^^^^^^^^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 116, in get_installed_libraries
     return {
            ^
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 116, in <dictcomp>
     return {
            ^
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 105, in get_template_tag_modules
     for name in get_package_libraries(pkg):
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 130, in get_package_libraries
     raise InvalidTemplateLibrary(
 django.template.library.InvalidTemplateLibrary: Invalid template library specified. ImportError raised when trying to load 'core.templatetags.custom_filters': cannot import name 'Undefined' from 'django.template.base' (/usr/local/lib/python3.11/site-packages/django/template/base.py)
 Traceback (most recent call last):
   File "/usr/local/lib/python3.11/site-packages/django/template/utils.py", line 69, in __getitem__
     return self._engines[alias]
            ~~~~~~~~~~~~~^^^^^^^
 KeyError: 'django'
 
 During handling of the above exception, another exception occurred:
 
 Traceback (most recent call last):
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 128, in get_package_libraries
     module = import_module(entry[1])
              ^^^^^^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/importlib/__init__.py", line 126, in import_module
     return _bootstrap._gcd_import(name[level:], package, level)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   File "<frozen importlib._bootstrap>", line 1204, in _gcd_import
   File "<frozen importlib._bootstrap>", line 1176, in _find_and_load
   File "<frozen importlib._bootstrap>", line 1147, in _find_and_load_unlocked
   File "<frozen importlib._bootstrap>", line 690, in _load_unlocked
   File "<frozen importlib._bootstrap_external>", line 940, in exec_module
   File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed
   File "/sisoc/core/templatetags/custom_filters.py", line 6, in <module>
     from django.template.base import Undefined
 ImportError: cannot import name 'Undefined' from 'django.template.base' (/usr/local/lib/python3.11/site-packages/django/template/base.py)
 
 The above exception was the direct cause of the following exception:
 
 Traceback (most recent call last):
   File "/sisoc/manage.py", line 38, in <module>
     main()
   File "/sisoc/manage.py", line 34, in main
     execute_from_command_line(sys.argv)
   File "/usr/local/lib/python3.11/site-packages/django/core/management/__init__.py", line 442, in execute_from_command_line
     utility.execute()
   File "/usr/local/lib/python3.11/site-packages/django/core/management/__init__.py", line 436, in execute
     self.fetch_command(subcommand).run_from_argv(self.argv)
   File "/usr/local/lib/python3.11/site-packages/django/core/management/base.py", line 412, in run_from_argv
     self.execute(*args, **cmd_options)
   File "/usr/local/lib/python3.11/site-packages/django/core/management/base.py", line 458, in execute
     output = self.handle(*args, **options)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/core/management/base.py", line 106, in wrapper
     res = handle_func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/core/management/commands/migrate.py", line 100, in handle
     self.check(databases=[database])
   File "/usr/local/lib/python3.11/site-packages/django/core/management/base.py", line 485, in check
     all_issues = checks.run_checks(
                  ^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/core/checks/registry.py", line 88, in run_checks
     new_errors = check(app_configs=app_configs, databases=databases)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/contrib/admin/checks.py", line 78, in check_dependencies
     for engine in engines.all():
                   ^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/template/utils.py", line 94, in all
     return [self[alias] for alias in self]
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/template/utils.py", line 94, in <listcomp>
     return [self[alias] for alias in self]
             ~~~~^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/template/utils.py", line 85, in __getitem__
     engine = engine_cls(params)
              ^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 24, in __init__
     options["libraries"] = self.get_templatetag_libraries(libraries)
                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 42, in get_templatetag_libraries
     libraries = get_installed_libraries()
                 ^^^^^^^^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 116, in get_installed_libraries
     return {
            ^
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 116, in <dictcomp>
     return {
            ^
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 105, in get_template_tag_modules
     for name in get_package_libraries(pkg):
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 130, in get_package_libraries
     raise InvalidTemplateLibrary(
 django.template.library.InvalidTemplateLibrary: Invalid template library specified. ImportError raised when trying to load 'core.templatetags.custom_filters': cannot import name 'Undefined' from 'django.template.base' (/usr/local/lib/python3.11/site-packages/django/template/base.py)
 Traceback (most recent call last):
   File "/usr/local/lib/python3.11/site-packages/django/template/utils.py", line 69, in __getitem__
     return self._engines[alias]
            ~~~~~~~~~~~~~^^^^^^^
 KeyError: 'django'
 
 During handling of the above exception, another exception occurred:
 
 Traceback (most recent call last):
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 128, in get_package_libraries
     module = import_module(entry[1])
              ^^^^^^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/importlib/__init__.py", line 126, in import_module
     return _bootstrap._gcd_import(name[level:], package, level)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   File "<frozen importlib._bootstrap>", line 1204, in _gcd_import
   File "<frozen importlib._bootstrap>", line 1176, in _find_and_load
   File "<frozen importlib._bootstrap>", line 1147, in _find_and_load_unlocked
   File "<frozen importlib._bootstrap>", line 690, in _load_unlocked
   File "<frozen importlib._bootstrap_external>", line 940, in exec_module
   File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed
   File "/sisoc/core/templatetags/custom_filters.py", line 6, in <module>
     from django.template.base import Undefined
 ImportError: cannot import name 'Undefined' from 'django.template.base' (/usr/local/lib/python3.11/site-packages/django/template/base.py)
 
 The above exception was the direct cause of the following exception:
 
 Traceback (most recent call last):
   File "/sisoc/manage.py", line 38, in <module>
     main()
   File "/sisoc/manage.py", line 34, in main
     execute_from_command_line(sys.argv)
   File "/usr/local/lib/python3.11/site-packages/django/core/management/__init__.py", line 442, in execute_from_command_line
     utility.execute()
   File "/usr/local/lib/python3.11/site-packages/django/core/management/__init__.py", line 436, in execute
     self.fetch_command(subcommand).run_from_argv(self.argv)
   File "/usr/local/lib/python3.11/site-packages/django/core/management/base.py", line 412, in run_from_argv
     self.execute(*args, **cmd_options)
   File "/usr/local/lib/python3.11/site-packages/django/core/management/base.py", line 458, in execute
     output = self.handle(*args, **options)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/core/management/base.py", line 106, in wrapper
     res = handle_func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/core/management/commands/migrate.py", line 100, in handle
     self.check(databases=[database])
   File "/usr/local/lib/python3.11/site-packages/django/core/management/base.py", line 485, in check
     all_issues = checks.run_checks(
                  ^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/core/checks/registry.py", line 88, in run_checks
     new_errors = check(app_configs=app_configs, databases=databases)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/contrib/admin/checks.py", line 78, in check_dependencies
     for engine in engines.all():
                   ^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/template/utils.py", line 94, in all
     return [self[alias] for alias in self]
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/template/utils.py", line 94, in <listcomp>
     return [self[alias] for alias in self]
             ~~~~^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/template/utils.py", line 85, in __getitem__
     engine = engine_cls(params)
              ^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 24, in __init__
     options["libraries"] = self.get_templatetag_libraries(libraries)
                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 42, in get_templatetag_libraries
     libraries = get_installed_libraries()
                 ^^^^^^^^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 116, in get_installed_libraries
     return {
            ^
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 116, in <dictcomp>
     return {
            ^
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 105, in get_template_tag_modules
     for name in get_package_libraries(pkg):
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 130, in get_package_libraries
     raise InvalidTemplateLibrary(
 django.template.library.InvalidTemplateLibrary: Invalid template library specified. ImportError raised when trying to load 'core.templatetags.custom_filters': cannot import name 'Undefined' from 'django.template.base' (/usr/local/lib/python3.11/site-packages/django/template/base.py)
 Traceback (most recent call last):
   File "/usr/local/lib/python3.11/site-packages/django/template/utils.py", line 69, in __getitem__
     return self._engines[alias]
            ~~~~~~~~~~~~~^^^^^^^
 KeyError: 'django'
 
 During handling of the above exception, another exception occurred:
 
 Traceback (most recent call last):
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 128, in get_package_libraries
     module = import_module(entry[1])
              ^^^^^^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/importlib/__init__.py", line 126, in import_module
     return _bootstrap._gcd_import(name[level:], package, level)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   File "<frozen importlib._bootstrap>", line 1204, in _gcd_import
   File "<frozen importlib._bootstrap>", line 1176, in _find_and_load
   File "<frozen importlib._bootstrap>", line 1147, in _find_and_load_unlocked
   File "<frozen importlib._bootstrap>", line 690, in _load_unlocked
   File "<frozen importlib._bootstrap_external>", line 940, in exec_module
   File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed
   File "/sisoc/core/templatetags/custom_filters.py", line 6, in <module>
     from django.template.base import Undefined
 ImportError: cannot import name 'Undefined' from 'django.template.base' (/usr/local/lib/python3.11/site-packages/django/template/base.py)
 
 The above exception was the direct cause of the following exception:
 
 Traceback (most recent call last):
   File "/sisoc/manage.py", line 38, in <module>
     main()
   File "/sisoc/manage.py", line 34, in main
     execute_from_command_line(sys.argv)
   File "/usr/local/lib/python3.11/site-packages/django/core/management/__init__.py", line 442, in execute_from_command_line
     utility.execute()
   File "/usr/local/lib/python3.11/site-packages/django/core/management/__init__.py", line 436, in execute
     self.fetch_command(subcommand).run_from_argv(self.argv)
   File "/usr/local/lib/python3.11/site-packages/django/core/management/base.py", line 412, in run_from_argv
     self.execute(*args, **cmd_options)
   File "/usr/local/lib/python3.11/site-packages/django/core/management/base.py", line 453, in execute
     self.check()
   File "/usr/local/lib/python3.11/site-packages/django/core/management/base.py", line 485, in check
     all_issues = checks.run_checks(
                  ^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/core/checks/registry.py", line 88, in run_checks
     new_errors = check(app_configs=app_configs, databases=databases)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/contrib/admin/checks.py", line 78, in check_dependencies
     for engine in engines.all():
                   ^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/template/utils.py", line 94, in all
     return [self[alias] for alias in self]
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/template/utils.py", line 94, in <listcomp>
     return [self[alias] for alias in self]
             ~~~~^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/template/utils.py", line 85, in __getitem__
     engine = engine_cls(params)
              ^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 24, in __init__
     options["libraries"] = self.get_templatetag_libraries(libraries)
                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 42, in get_templatetag_libraries
     libraries = get_installed_libraries()
                 ^^^^^^^^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 116, in get_installed_libraries
     return {
            ^
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 116, in <dictcomp>
     return {
            ^
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 105, in get_template_tag_modules
     for name in get_package_libraries(pkg):
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 130, in get_package_libraries
     raise InvalidTemplateLibrary(
 django.template.library.InvalidTemplateLibrary: Invalid template library specified. ImportError raised when trying to load 'core.templatetags.custom_filters': cannot import name 'Undefined' from 'django.template.base' (/usr/local/lib/python3.11/site-packages/django/template/base.py)
 Traceback (most recent call last):
   File "/usr/local/lib/python3.11/site-packages/django/template/utils.py", line 69, in __getitem__
     return self._engines[alias]
            ~~~~~~~~~~~~~^^^^^^^
 KeyError: 'django'
 
 During handling of the above exception, another exception occurred:
 
 Traceback (most recent call last):
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 128, in get_package_libraries
     module = import_module(entry[1])
              ^^^^^^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/importlib/__init__.py", line 126, in import_module
     return _bootstrap._gcd_import(name[level:], package, level)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   File "<frozen importlib._bootstrap>", line 1204, in _gcd_import
   File "<frozen importlib._bootstrap>", line 1176, in _find_and_load
   File "<frozen importlib._bootstrap>", line 1147, in _find_and_load_unlocked
   File "<frozen importlib._bootstrap>", line 690, in _load_unlocked
   File "<frozen importlib._bootstrap_external>", line 940, in exec_module
   File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed
   File "/sisoc/core/templatetags/custom_filters.py", line 6, in <module>
     from django.template.base import Undefined
 ImportError: cannot import name 'Undefined' from 'django.template.base' (/usr/local/lib/python3.11/site-packages/django/template/base.py)
 
 The above exception was the direct cause of the following exception:
 
 Traceback (most recent call last):
   File "/sisoc/manage.py", line 38, in <module>
     main()
   File "/sisoc/manage.py", line 34, in main
     execute_from_command_line(sys.argv)
   File "/usr/local/lib/python3.11/site-packages/django/core/management/__init__.py", line 442, in execute_from_command_line
     utility.execute()
   File "/usr/local/lib/python3.11/site-packages/django/core/management/__init__.py", line 436, in execute
     self.fetch_command(subcommand).run_from_argv(self.argv)
   File "/usr/local/lib/python3.11/site-packages/django/core/management/base.py", line 412, in run_from_argv
     self.execute(*args, **cmd_options)
   File "/usr/local/lib/python3.11/site-packages/django/core/management/base.py", line 453, in execute
     self.check()
   File "/usr/local/lib/python3.11/site-packages/django/core/management/base.py", line 485, in check
     all_issues = checks.run_checks(
                  ^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/core/checks/registry.py", line 88, in run_checks
     new_errors = check(app_configs=app_configs, databases=databases)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/contrib/admin/checks.py", line 78, in check_dependencies
     for engine in engines.all():
                   ^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/template/utils.py", line 94, in all
     return [self[alias] for alias in self]
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/template/utils.py", line 94, in <listcomp>
     return [self[alias] for alias in self]
             ~~~~^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/template/utils.py", line 85, in __getitem__
     engine = engine_cls(params)
              ^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 24, in __init__
     options["libraries"] = self.get_templatetag_libraries(libraries)
                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 42, in get_templatetag_libraries
     libraries = get_installed_libraries()
                 ^^^^^^^^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 116, in get_installed_libraries
     return {
            ^
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 116, in <dictcomp>
     return {
            ^
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 105, in get_template_tag_modules
     for name in get_package_libraries(pkg):
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 130, in get_package_libraries
     raise InvalidTemplateLibrary(
 django.template.library.InvalidTemplateLibrary: Invalid template library specified. ImportError raised when trying to load 'core.templatetags.custom_filters': cannot import name 'Undefined' from 'django.template.base' (/usr/local/lib/python3.11/site-packages/django/template/base.py)
 Traceback (most recent call last):
   File "/usr/local/lib/python3.11/site-packages/django/template/utils.py", line 69, in __getitem__
     return self._engines[alias]
            ~~~~~~~~~~~~~^^^^^^^
 KeyError: 'django'
 
 During handling of the above exception, another exception occurred:
 
 Traceback (most recent call last):
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 128, in get_package_libraries
     module = import_module(entry[1])
              ^^^^^^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/importlib/__init__.py", line 126, in import_module
     return _bootstrap._gcd_import(name[level:], package, level)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   File "<frozen importlib._bootstrap>", line 1204, in _gcd_import
   File "<frozen importlib._bootstrap>", line 1176, in _find_and_load
   File "<frozen importlib._bootstrap>", line 1147, in _find_and_load_unlocked
   File "<frozen importlib._bootstrap>", line 690, in _load_unlocked
   File "<frozen importlib._bootstrap_external>", line 940, in exec_module
   File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed
   File "/sisoc/core/templatetags/custom_filters.py", line 6, in <module>
     from django.template.base import Undefined
 ImportError: cannot import name 'Undefined' from 'django.template.base' (/usr/local/lib/python3.11/site-packages/django/template/base.py)
 
 The above exception was the direct cause of the following exception:
 
 Traceback (most recent call last):
   File "/sisoc/manage.py", line 38, in <module>
     main()
   File "/sisoc/manage.py", line 34, in main
     execute_from_command_line(sys.argv)
   File "/usr/local/lib/python3.11/site-packages/django/core/management/__init__.py", line 442, in execute_from_command_line
     utility.execute()
   File "/usr/local/lib/python3.11/site-packages/django/core/management/__init__.py", line 436, in execute
     self.fetch_command(subcommand).run_from_argv(self.argv)
   File "/usr/local/lib/python3.11/site-packages/django/core/management/base.py", line 412, in run_from_argv
     self.execute(*args, **cmd_options)
   File "/usr/local/lib/python3.11/site-packages/django/core/management/base.py", line 453, in execute
     self.check()
   File "/usr/local/lib/python3.11/site-packages/django/core/management/base.py", line 485, in check
     all_issues = checks.run_checks(
                  ^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/core/checks/registry.py", line 88, in run_checks
     new_errors = check(app_configs=app_configs, databases=databases)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/contrib/admin/checks.py", line 78, in check_dependencies
     for engine in engines.all():
                   ^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/template/utils.py", line 94, in all
     return [self[alias] for alias in self]
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/template/utils.py", line 94, in <listcomp>
     return [self[alias] for alias in self]
             ~~~~^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/template/utils.py", line 85, in __getitem__
     engine = engine_cls(params)
              ^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 24, in __init__
     options["libraries"] = self.get_templatetag_libraries(libraries)
                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 42, in get_templatetag_libraries
     libraries = get_installed_libraries()
                 ^^^^^^^^^^^^^^^^^^^^^^^^^
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 116, in get_installed_libraries
     return {
            ^
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 116, in <dictcomp>
     return {
            ^
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 105, in get_template_tag_modules
     for name in get_package_libraries(pkg):
   File "/usr/local/lib/python3.11/site-packages/django/template/backends/django.py", line 130, in get_package_libraries
     raise InvalidTemplateLibrary(
 django.template.library.InvalidTemplateLibrary: Invalid template library specified. ImportError raised when trying to load 'core.templatetags.custom_filters': cannot import name 'Undefined' from 'django.template.base' (/usr/local/lib/python3.11/site-packages/django/template/base.py)