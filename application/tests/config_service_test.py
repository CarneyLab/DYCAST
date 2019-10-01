import unittest
import os
import configparser

from services import config_service

class TestConfigServiceFunctions(unittest.TestCase):
    def test_get_env_variable(self):
        test_var = "TEST_VAR"
        expected_value = "Test 1 2 3"
        os.environ[test_var] = expected_value

        actual_value = config_service.get_env_variable(test_var)

        self.assertEqual(actual_value, expected_value)

    def test_get_env_variable_missing(self):
        test_var = "NON_EXISTING_ENV_VAR"

        actual_value = config_service.get_env_variable(test_var)

        self.assertEqual(actual_value, None)

    def test_init_config(self):
        config_service.init_config()

        config = config_service.get_config()
        self.assertIsNotNone(config)

        expected_value = "dycast_log.txt"
        actual_value = config.get("system", "logfile")
        self.assertIsNotNone(actual_value)
        self.assertEqual(actual_value, expected_value)

    def test_get_alembic_config_path(self):
        current_directory = os.path.dirname(os.path.realpath(__file__))
        expected_value = os.path.join(current_directory, '..', 'init', 'migrations', 'alembic.ini')
        
        actual_value = config_service.get_alembic_config_path()
        self.assertEqual(os.path.abspath(actual_value), os.path.abspath(expected_value))
