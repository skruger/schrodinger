import logging
import uuid


class ContextCollectorRegistry(object):
    collectors = dict()

    @classmethod
    def distribute(cls, record):
        for collector in cls.collectors.values():
            collector.add_log_message(record)

    @classmethod
    def add_collector(cls, collector_id, collector):
        cls.collectors[collector_id] = collector

    @classmethod
    def remove_collector(cls, collector_id):
        del cls.collectors[collector_id]


class LogCollector(object):
    def __init__(self, log_level=logging.INFO):
        self.log_level = log_level
        self._log_messages = list()
        self.id = uuid.uuid4().hex

    def add_log_message(self, record):
        self._log_messages.append(record)

    def get_log_messages(self):
        return self._log_messages

    def __enter__(self):
        ContextCollectorRegistry.add_collector(self.id, self)

    def __exit__(self, exc_type, exc_val, exc_tb):
        ContextCollectorRegistry.remove_collector(self.id)


class LogCollectorHandler(logging.Handler):
    def emit(self, record):
        ContextCollectorRegistry.distribute(self.format(record))
