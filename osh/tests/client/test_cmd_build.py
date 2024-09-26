import io
import optparse
import unittest
from unittest.mock import MagicMock, patch

from osh.client.commands.cmd_build import Base_Build

option_patches = [
    "osh.client.commands.common.add_analyzers_option",
    "osh.client.commands.common.add_comment_option",
    "osh.client.commands.common.add_comp_warnings_option",
    "osh.client.commands.common.add_config_option",
    "osh.client.commands.common.add_csmock_args_option",
    "osh.client.commands.common.add_custom_model_option",
    "osh.client.commands.common.add_download_results_option",
    "osh.client.commands.common.add_email_to_option",
    "osh.client.commands.common.add_install_to_chroot_option",
    "osh.client.commands.common.add_json_option",
    "osh.client.commands.common.add_nowait_option",
    "osh.client.commands.common.add_nvr_option",
    "osh.client.commands.common.add_priority_option",
    "osh.client.commands.common.add_profile_option",
    "osh.client.commands.common.add_task_id_file_option"
]


class TestBaseBuild(unittest.TestCase):
    def setUp(self):
        # OSHCLITestBase.setup_cmd works only for enabled plugins
        parser = optparse.OptionParser()
        parser.add_option = MagicMock()

        self.command = Base_Build(parser=parser)
        self.command.hub = MagicMock()
        self.command.container = MagicMock()
        self.command.normalized_name = "build"

    @patch.multiple('osh.client.commands.common',
                    **{opt.split('.')[-1]: patch(opt) for opt in option_patches})
    def test_options(self):
        self.command.options()
        assert self.command.parser.usage == f"%prog {self.command.normalized_name} [options] <args>"
        assert self.command.parser.epilog == (
            "User configuration file is located at: "
            "~/.config/osh/client.conf"
        )

    @patch("osh.client.conf.Conf")
    def test_check_build_config_missing(self, MockConf):
        mock_conf_instance = MockConf.return_value
        mock_conf_instance.get_default_mockconfig.return_value = None

        with patch('sys.stderr', new=io.StringIO()) as fake_err:
            with self.assertRaises(SystemExit) as cm:
                self.command.check_build(args=None, kwargs={})
            self.assertEqual(cm.exception.code, 2)
            error_message = fake_err.getvalue()
            self.assertIn("You haven't specified mock config", error_message)

    def test_check_build_verify_mock_failed(self):
        conf_name = "rhel-7-x86_64"

        with patch('sys.stderr', new=io.StringIO()) as fake_err:
            # simulate the mock config does not exist
            self.command.hub.mock_config.get.return_value = None
            with self.assertRaises(SystemExit) as cm:
                self.command.check_build(args=None, kwargs={"config": conf_name})
            self.assertEqual(cm.exception.code, 2)
            self.assertIn(f"Mock config {conf_name} does not exist", fake_err.getvalue())

            # simulate mock config disabled
            self.command.hub.mock_config.get.return_value = {"enabled": False}
            with self.assertRaises(SystemExit) as cm:
                self.command.check_build(args=None, kwargs={"config": conf_name})
            self.assertEqual(cm.exception.code, 2)
            self.assertIn(f"Mock config {conf_name} is not enabled", fake_err.getvalue())

    def test_check_build_with_nvr_verify_koji_build_failed(self):
        conf_name = "rhel-7-x86_64"

        with patch('sys.stderr', new=io.StringIO()) as fake_err, \
             patch('osh.client.commands.shortcuts.verify_koji_build') as fake_verify_koji_build:
            nvr = "foo-1.0.0-1.el8"
            self.command.hub.mock_config.get.return_value = {"enabled": True}
            error_message = f"Build {nvr} does not exist"
            fake_verify_koji_build.return_value = error_message
            with self.assertRaises(SystemExit) as cm:
                kwargs = {"config": conf_name, "nvr": nvr}
                self.command.check_build(args=None, kwargs=kwargs)
            self.assertEqual(cm.exception.code, 2)
            self.assertIn(error_message, fake_err.getvalue())

    def test_check_build_with_non_existent_srpm(self):
        conf_name = "rhel-7-x86_64"

        with patch('sys.stderr', new=io.StringIO()) as fake_err, \
             patch('osh.client.commands.shortcuts.verify_koji_build') as fake_verify_koji_build:
            srpm = "/path/to/non-existent-srpm"
            self.command.hub.mock_config.get.return_value = {"enabled": True}
            error_message = f"file does not exist: {srpm}"
            fake_verify_koji_build.return_value = error_message
            with self.assertRaises(SystemExit) as cm:
                kwargs = {"config": conf_name, "srpm": srpm}
                self.command.check_build(args=None, kwargs=kwargs)
            self.assertEqual(cm.exception.code, 2)
            self.assertIn(error_message, fake_err.getvalue())

    def test_check_build_with_invalid_srpm_suffix(self):
        conf_name = "rhel-7-x86_64"

        with patch('sys.stderr', new=io.StringIO()) as fake_err, \
             patch('os.path.exists') as fake_path_exists:
            # srpm without the '.src.rpm' suffix
            srpm = "/path/to/foo.srpm"
            self.command.hub.mock_config.get.return_value = {"enabled": True}
            self.command.hub.upload_file.return_value = (1, 200, "")
            fake_path_exists.return_value = True
            error_message = f"provided file doesn't appear to be an SRPM: {srpm}"
            with self.assertRaises(SystemExit) as cm:
                kwargs = {
                    "config": conf_name,
                    "srpm": srpm,
                    # "tarball_build_script": "my-custom-script"
                }
                self.command.check_build(args=None, kwargs=kwargs)
            self.assertEqual(cm.exception.code, 2)
            self.assertIn(error_message, fake_err.getvalue())

    def test_check_build_success(self):
        conf_name = "rhel-7-x86_64"

        with patch('os.path.exists') as fake_path_exists:
            fake_path_exists.return_value = True
            # srpm without the '.src.rpm' suffix
            srpm = "/path/to/foo.src.srpm"
            self.command.hub.mock_config.get.return_value = {"enabled": True}
            self.command.hub.upload_file.return_value = (1, 200, "")
            fake_path_exists.return_value = True
            kwargs = {
                "config": conf_name,
                "srpm": srpm,
                "tarball_build_script": "my-custom-script"
            }
            options = self.command.check_build(args=None, kwargs=kwargs)
            expected_output = {
                'mock_config': 'rhel-7-x86_64',
                'tarball_build_script': 'my-custom-script',
                'upload_id': 1
            }
            self.assertEqual(options, expected_output)

    def test_prepare_task_options_priority_error(self):
        kwargs = {"priority": -1}
        with patch('sys.stderr', new=io.StringIO()) as fake_err:
            error_message = "Priority must be a non-negative number!"
            with self.assertRaises(SystemExit) as cm:
                self.command.prepare_task_options(args=None, kwargs=kwargs)
            self.assertEqual(cm.exception.code, 2)
            self.assertIn(error_message, fake_err.getvalue())

    def test_prepare_task_options_check_analyzers_error(self):
        self.command.hub.mock_config.get.return_value = {"enabled": False}
        self.command.check_build = MagicMock()
        self.command.check_build.return_value = {
            'mock_config': 'rhel-7-x86_64',
            'tarball_build_script': 'my-custom-script',
            'upload_id': 1
        }
        kwargs = {
            "analyzers": ["snyk", "cppcheck"],
            "email_to": "admin@example.com",
            "priority": 1,
            "warn_level": 3,
            "comment": "my comment"
        }
        with patch('sys.stderr', new=io.StringIO()) as fake_err:
            error_message = "Check analyzer failed"
            # force return of string to simulate the RuntimeError
            self.command.hub.scan.check_analyzers.return_value = error_message
            with self.assertRaises(SystemExit) as cm:
                self.command.prepare_task_options(args=None, kwargs=kwargs)
            self.assertEqual(cm.exception.code, 2)
            self.assertIn(error_message, fake_err.getvalue())

    def test_prepare_task_options_profile_does_not_exist_error(self):
        self.command.hub.mock_config.get.return_value = {"enabled": False}
        self.command.check_build = MagicMock()
        self.command.check_build.return_value = {
            'mock_config': 'rhel-7-x86_64',
            'tarball_build_script': 'my-custom-script',
            'upload_id': 1
        }
        self.command.hub.scan.check_analyzers.return_value = None
        self.command.hub.upload_file.return_value = (1, 200, "")
        profile_name = "default"
        kwargs = {
            "analyzers": ["snyk", "cppcheck"],
            "email_to": "admin@example.com",
            "priority": 1,
            "warn_level": 3,
            "comment": "my comment",
            "profile": profile_name,
            "csmock_args": "--keep-going",
            "cov_custom_model": "fake_model",
            "packages_to_install": "pkg1",
            "install_to_chroot": True
        }

        self.command.hub.scan.list_profiles.return_value = [{"name": "default"}]
        options = self.command.prepare_task_options(args=None, kwargs=kwargs)
        expected_retval = kwargs

        # keys below are not included in the return value
        for k in ["cov_custom_model", "packages_to_install", "warn_level"]:
            expected_retval.pop(k)

        # data below are included
        expected_retval.update(self.command.check_build.return_value)
        expected_retval.update({'upload_model_id': 1, 'warning_level': 3})
        self.assertEqual(options, expected_retval)

    def test_run_with_invalid_results_dir(self):
        self.command.connect_to_hub = MagicMock()
        self.command.hub.mock_config.get.return_value = {"enabled": False}
        self.command.prepare_task_options = MagicMock()
        self.command.prepare_task_options.return_value = {
            'mock_config': 'rhel-7-x86_64',
            'tarball_build_script': 'my-custom-script',
            'upload_id': 1
        }
        results_dir = "/path/to/non-existent-dir/"
        kwargs = {"results_dir": results_dir}
        error_message = f"{results_dir} is not a valid directory!"
        with patch('sys.stderr', new=io.StringIO()) as fake_err:
            with self.assertRaises(SystemExit) as cm:
                self.command.run(args=None, **kwargs)
            self.assertEqual(cm.exception.code, 2)
            self.assertIn(error_message, fake_err.getvalue())

    def test_run_with_or_without_json(self):
        self.command.connect_to_hub = MagicMock()
        self.command.hub.mock_config.get.return_value = {"enabled": False}
        self.command.hub.client.task_url.return_value = "http://osh/tasks/1"
        self.command.prepare_task_options = MagicMock()
        self.command.prepare_task_options.return_value = {
            'mock_config': 'rhel-7-x86_64',
            'tarball_build_script': 'my-custom-script',
            'upload_id': 1
        }
        self.command.submit_task = MagicMock()
        self.command.submit_task.return_value = 1
        self.command.write_task_id_file = MagicMock()

        # with json
        kwargs = {"nowait": True, "json": True}
        expected_output = '{"id": 1, "url": "http://osh/tasks/1"}'
        with patch('sys.stdout', new=io.StringIO()) as fake_out:
            self.command.run(args=None, **kwargs)
            self.assertEqual(expected_output, fake_out.getvalue().strip())

        # without json
        kwargs = {"nowait": True}
        expected_output = "Task info: http://osh/tasks/1"
        with patch('sys.stdout', new=io.StringIO()) as fake_out:
            self.command.run(args=None, **kwargs)
            self.assertEqual(expected_output, fake_out.getvalue().strip())

    def test_submit_task(self):
        with self.assertRaises(NotImplementedError):
            self.command.submit_task(options={})
