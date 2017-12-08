import unittest
import logging

from logging.config import dictConfig

from schrodinger.log import LogCollector, ContextCollectorRegistry

LOGGING = {
    'version': 1,
    'formatters': {
        'verbose': {
            'format': 'schrodinger[%(process)d]: %(levelname)s %(name)s[%(module)s] %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'level': 'DEBUG',
        },
        'collector': {
            'class': 'schrodinger.log.LogCollectorHandler',
            'formatter': 'verbose',
            'level': 'DEBUG',
        },
    },
    'loggers': {
        '': {
            'level': 'INFO',
            'handlers': ['console', 'collector'],
            'propagate': False,
        },
    },
}


dictConfig(LOGGING)


class LogTestCase(unittest.TestCase):
    def test_logger_context(self):
        log = logging.getLogger(__name__)

        log_collector = LogCollector()
        with log_collector:
            self.assertIn(log_collector, ContextCollectorRegistry.collectors.values())
            log.info("This is a log message")
            log.error("This is an error with an arg: %s", "123")

        self.assertNotIn(log_collector, ContextCollectorRegistry.collectors.values())
        messages = log_collector.get_log_messages()

        self.assertEqual(len(messages), 2)

        self.assertIn("This is a log message", messages[0])
        self.assertIn("This is an error with an arg: 123", messages[1])
