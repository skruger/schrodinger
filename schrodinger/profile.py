import logging
import os
import random
import socket
import tempfile
import time
from datetime import datetime

import boto3

log = logging.getLogger(__name__)


class ProfilerConfig(object):
    default_bucket = None
    default_path = "Profiler"
    default_region = "us-east-1"

    def __init__(self, bucket=None, path=None, region=None, access_key_id=None, secret_key=None):
        self.bucket = bucket or self.default_bucket or os.environ.get('SCHRODINGER_BUCKET')
        self.path = path or self.default_path
        self.region = region or self.default_region
        self.access_key_id = access_key_id
        self.secret_key = secret_key


class Profiler(object):
    """
    Profiler allows a function to be instrumented with a profiler that executes depending on
    a configured probability.  Profiler can be used both as a decorator and a context manager.
    Profiling data is collected and uploaded to an S3 bucket.  The default bucket and path is
    <SITE.s3.bucket_priv>/Profiler.

    Subclass configurable options:
    default_profiler_config_class
        A subclass of ProfilerConfig with default_bucket, default_path, or default_region set.
        Subclassing Profiler and providing this option will allow the subclass to be used without
        passing in a profiler_config.

    Arguments:
    name
        The name of the function to be profiled.  This value is used in generating directories
        and filenames when uploading to S3.

    probability
        The configured probability can be a float between 0 and 1 or a callable that returns
        a True or False if the profiler should run.

    profiler_config
        A ProfilerConfig object can be supplied to set S3 configuration options
    """
    default_profiler_config_class = ProfilerConfig

    def __init__(self, name, probability=0.01, profiler_config=None):
        self.profiler = None
        self.start_time = None
        self.duration = None
        self.name = name
        self.Profile = None
        self.probability = 0  # If there is a problem importing cProfile disable profiling
        try:
            # Importing locally keeps this code safe to run even if cPython is not available
            from cProfile import Profile
            self.Profile = Profile
            # Only set probability once we know the profiler is available
            self.probability = probability
        except ImportError:
            log.error("Profiler disabled for %s, cProfile could not be imported!", name)
        self.fn_name = None
        self.profiler_active = False

        self.config = profiler_config or self.default_profiler_config_class()

        assert isinstance(self.config, ProfilerConfig), "profiler_config must be instance of ProfilerConfig"

    def __call__(self, fn):
        def wrapped(*args, **kwargs):
            with self:
                self.fn_name = fn.__name__
                return fn(*args, **kwargs)

        return wrapped

    def __enter__(self):
        try:
            self.profiler_active = False
            if self.should_profile():
                assert self.config.bucket, "No profiling output bucket configured!"
                self.profiler_active = True
                self.profiler = self.Profile()
                self.start_time = time.time()
                self.profiler.enable()
        except:
            log.exception("Unable to start profiling for %s!", self.name)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.profiler_active:
            try:
                self.profiler_active = False
                self.duration = time.time() - self.start_time
                with tempfile.NamedTemporaryFile() as stats_file:
                    self.profiler.dump_stats(stats_file.name)
                    self.upload_file(stats_file.name)
            except:
                log.exception("Unable to write profiling output for %s!", self.name)

    def should_profile(self):
        if callable(self.probability):
            return self.probability()
        else:
            return random.uniform(0, 1) < self.probability

    def get_s3_client(self):
        client = boto3.client(
            's3',
            region_name=self.config.region,
            aws_access_key_id=self.config.access_key_id,
            aws_secret_access_key=self.config.secret_key,
        )
        return client

    def upload_file(self, filename):
        s3 = self.get_s3_client()
        key = self.get_key()
        log.info("Uploading profiler output for %s to %s/%s",
                 self.name, self.config.bucket, key)
        s3.upload_file(filename, self.config.bucket, key)

    def get_key(self):
        key = "{path}/{name}/{date}/{name}-{hostname}-start{time:.0f}-dur{duration:.2f}.pstat"
        return key.format(
            path=self.config.path,
            name=self.name,
            date=datetime.now().strftime("%Y-%m-%d"),
            hostname=socket.gethostname(),
            time=self.start_time,
            duration=self.duration,
        )
