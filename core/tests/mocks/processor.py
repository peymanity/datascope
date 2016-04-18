from core.utils.configuration import ConfigurationProperty
from datascope.configuration import MOCK_CONFIGURATION
from core.processors.base import Processor


class MockProcessor(Processor):

    config = ConfigurationProperty(
        storage_attribute="_config",
        defaults=MOCK_CONFIGURATION,
        namespace="mock_processor",
        private=[]
    )


class MockNumberProcessor(MockProcessor):

    def number_individuals(self, individuals):
        def number_individual(individual, number):
            individual["number"] = number
            return individual
        return (number_individual(individual, idx+1) for idx, individual in enumerate(individuals))


class MockFilterProcessor(MockProcessor):

    def filter_individuals(self, individuals):
        for individual in individuals:
            if self.config.include_odd and individual.get("number") % 2:
                yield individual
            elif self.config.include_even and not individual.get("number") % 2:
                yield individual
            elif self.config.include_odd and self.config.include_even:
                yield individual
