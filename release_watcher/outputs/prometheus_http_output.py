import logging
from typing import Dict, Sequence
from prometheus_client import Gauge, start_http_server
from release_watcher.outputs.output_manager \
    import Output, OutputConfig, OutputType
from release_watcher.watchers import watcher_models

logger = logging.getLogger(__name__)

OUTPUT_NAME = 'prometheus_http'


class PrometheusHttpOutputConfig(OutputConfig):
    """Class to store the configuration for a PrometheusHttpOutput"""

    port: int = None

    def __init__(self, port: int):
        super().__init__(OUTPUT_NAME)
        self.port = port

    def __str__(self) -> str:
        return '%s' % (self.port)

    def __repr__(self) -> str:
        return 'PrometheusHttpOutputConfig(%s)' % self


class PrometheusHttpOutput(Output):
    """Implementation of an Output that exposes Prometheus metrics"""

    server_started: bool = False
    missed_releases_gauge: Gauge = None

    def __init__(self, config: PrometheusHttpOutputConfig):
        super().__init__(config)

    def outputs(self, results: Sequence[watcher_models.WatchResult]):
        logger.debug("Exposing results on %d" % self.config.port)

        if not self.server_started:
            logger.info("Starting Prometheus HTTP Server on port %d" %
                        self.config.port)
            start_http_server(self.config.port)
            self.server_started = True

        if not self.missed_releases_gauge:
            logger.debug("Initializing missed_releases_gauge")
            self.missed_releases_gauge = Gauge('missed_releases',
                                               'Number of missed releases',
                                               ['name'])

        for result in results:
            self.missed_releases_gauge.labels(str(result.config)).set(
                len(result.missed_releases))


class PrometheusHttpOutputType(OutputType):
    """Class to represent the PrometheusHttpOutput type of Output"""

    def __init__(self):
        super().__init__(OUTPUT_NAME)

    def parse_config(self, global_conf: Dict,
                     source_config: Dict) -> PrometheusHttpOutputConfig:
        port = source_config.get('port', 8080)

        if not isinstance(port, int):
            logger.warning("port '%s' is not a number, falling back to %d" %
                           (port, 8080))
            port = 8080

        return PrometheusHttpOutputConfig(port)

    def create_output(self, config: OutputConfig) -> PrometheusHttpOutput:
        return PrometheusHttpOutput(config)