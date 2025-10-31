import io
import logging
import sys
import unittest

from src.amplitude_experiment.local.config import LocalEvaluationConfig


class LocalEvaluationConfigLoggerTestCase(unittest.TestCase):
    """Tests for LocalEvaluationConfig logger configuration"""

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
        config = LocalEvaluationConfig(debug=False)
        self.assertEqual(config.logger.level, logging.WARNING)
        self.assertEqual(len(config.logger.handlers), 1)
        handler = config.logger.handlers[0]
        self.assertIsInstance(handler, logging.StreamHandler)
        self.assertEqual(handler.stream, sys.stderr)

    def test_default_logger_has_debug_level_when_debug_true(self):
        """Test that default logger has DEBUG level when debug=True"""
        config = LocalEvaluationConfig(debug=True)
        self.assertEqual(config.logger.level, logging.DEBUG)

    def test_custom_logger_is_used(self):
        """Test that provided custom logger is used"""
        custom_logger = logging.getLogger("CustomLogger")
        config = LocalEvaluationConfig(logger=custom_logger)
        self.assertEqual(config.logger, custom_logger)
        self.assertEqual(config.logger.name, "CustomLogger")

    def test_custom_logger_level_not_modified_by_debug_flag(self):
        """Test that custom logger level is not modified by debug flag"""
        # Test with debug=True
        custom_logger = logging.getLogger("CustomLoggerDebug")
        custom_logger.setLevel(logging.ERROR)
        config = LocalEvaluationConfig(debug=True, logger=custom_logger)
        # Logger level should remain unchanged (ERROR), not modified to DEBUG
        self.assertEqual(config.logger.level, logging.ERROR)
        
        # Test with debug=False
        custom_logger2 = logging.getLogger("CustomLoggerWarning")
        custom_logger2.setLevel(logging.INFO)
        config2 = LocalEvaluationConfig(debug=False, logger=custom_logger2)
        # Logger level should remain unchanged (INFO), not modified to WARNING
        self.assertEqual(config2.logger.level, logging.INFO)

    def test_default_logger_only_one_handler_added(self):
        """Test that only one handler is added to default logger"""
        config1 = LocalEvaluationConfig()
        config2 = LocalEvaluationConfig()
        # Both should use the same logger instance (singleton)
        logger = logging.getLogger("Amplitude")
        # Should only have one handler even after creating multiple configs
        self.assertEqual(len(logger.handlers), 1)

if __name__ == '__main__':
    unittest.main()
