import logging

from path import path

from changes import config, probe, shell, util, venv, verification

log = logging.getLogger(__name__)


def install():
    module_name, dry_run, new_version = config.common_arguments()
    build_package_command = 'python setup.py clean sdist'
    if probe.has_requirement('wheel'):
        build_package_command += ' bdist_wheel'

    try:
        result = shell.dry_run(build_package_command)
        if not dry_run and shell.dry_run(build_package_command).succeeded:
            with util.mktmpdir() as tmp_dir:
                venv.create_venv(tmp_dir=tmp_dir)
                for distribution in path('dist').files():
                    venv.install(distribution, tmp_dir)
                    log.info('Successfully installed %s sdist', module_name)
                    if verification.run_test_command():
                        log.info('Successfully ran test command: %s',
                                 config.arguments['--test-command'])
    except Exception, e:
        raise Exception('Error installing distribution %s' % distribution, e)


def upload():
    module_name, dry_run, new_version = config.common_arguments()
    pypi = config.arguments['--pypi']

    upload_args = 'python setup.py clean sdist upload'
    if pypi:
        upload_args += ' -r %s' % pypi

    upload_result = shell.dry_run(upload_args)
    if not dry_run and upload_result.failed:
        raise Exception('Error uploading: %s' % upload_result)
    else:
        log.info('Successfully uploaded %s %s', module_name, new_version)


def pypi():
    module_name, dry_run, _ = config.common_arguments()

    tmp_dir = venv.create_venv()
    install_cmd = '%s/bin/pip install %s' % (tmp_dir, module_name)

    package_index = 'pypi'
    pypi = config.arguments['--pypi']
    if pypi:
        install_cmd += '-i %s' % pypi
        package_index = pypi

    try:
        result = shell.dry_run(install_cmd)
        if not dry_run and result.failed:
            log.error('Failed to install %s from %s',
                      module_name, package_index)
        else:
            log.info('Successfully installed %s from %s',
                     module_name, package_index)

        verification.run_test_command()
    except Exception, e:
        error_msg = 'Error installing %s from %s' % (module_name, package_index)
        log.exception(error_msg)
        raise Exception(error_msg, e)

    path(tmp_dir).rmtree(path(tmp_dir))
