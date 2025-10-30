import io
import logging
import sys
import unittest

from src.amplitude_experiment.remote.config import RemoteEvaluationConfig


class RemoteEvaluationConfigLoggerTestCase(unittest.TestCase):
    """Tests for RemoteEvaluationConfig logger configuration"""

    def setUp(self):
        """Clear existing handlers from the Amplitude logger before each test"""
        logger = logging.getLogger("Amplitude")
        logger.handlers.clear()
        logger.setLevel(logging.NOTSET)

    def tearDown(self):
        """Clean up handlers after each test"""
        logger = logging.getLogger("Amplitude")
        logger.handlers.clear()

    def test_default_logger_has_warning_level(self):
        """Test that default logger has WARNING level and stderr handler when debug=False"""
        config = RemoteEvaluationConfig(debug=False)
        self.assertEqual(config.logger.level, logging.WARNING)
        self.assertEqual(len(config.logger.handlers), 1)
        handler = config.logger.handlers[0]
        self.assertIsInstance(handler, logging.StreamHandler)
        self.assertEqual(handler.stream, sys.stderr)

    def test_default_logger_has_debug_level_when_debug_true(self):
        """Test that default logger has DEBUG level when debug=True"""
        config = RemoteEvaluationConfig(debug=True)
        self.assertEqual(config.logger.level, logging.DEBUG)

    def test_custom_logger_is_used(self):
        """Test that provided custom logger is used"""
        custom_logger = logging.getLogger("CustomLogger")
        config = RemoteEvaluationConfig(logger=custom_logger)
        self.assertEqual(config.logger, custom_logger)
        self.assertEqual(config.logger.name, "CustomLogger")

    def test_custom_logger_has_debug_level_when_debug_true(self):
        """Test that custom logger has DEBUG level set when debug=True"""
        custom_logger = logging.getLogger("CustomLogger")
        config = RemoteEvaluationConfig(debug=True, logger=custom_logger)
        self.assertEqual(config.logger.level, logging.DEBUG)

    def test_custom_logger_has_warning_level_when_debug_false(self):
        """Test that custom logger has WARNING level set when debug=False"""
        custom_logger = logging.getLogger("CustomLogger")
        config = RemoteEvaluationConfig(debug=False, logger=custom_logger)
        self.assertEqual(config.logger.level, logging.WARNING)

    def test_custom_logger_debug_flag_takes_precedence(self):
        """Test that debug flag takes precedence over logger's existing level"""
        custom_logger = logging.getLogger("CustomLogger")
        custom_logger.setLevel(logging.ERROR)
        config = RemoteEvaluationConfig(debug=True, logger=custom_logger)
        # Debug flag should override to DEBUG
        self.assertEqual(config.logger.level, logging.DEBUG)

    def test_default_logger_only_one_handler_added(self):
        """Test that only one handler is added to default logger"""
        config1 = RemoteEvaluationConfig()
        config2 = RemoteEvaluationConfig()
        # Both should use the same logger instance (singleton)
        logger = logging.getLogger("Amplitude")
        # Should only have one handler even after creating multiple configs
        self.assertEqual(len(logger.handlers), 1)

if __name__ == '__main__':
    unittest.main()
