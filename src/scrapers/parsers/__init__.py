"""Job parsers for different platforms."""
from .base_parser import BaseJobParser
from .comeet_parser import ComeetParser
from .greenhouse_parser import GreenhouseParser
from .api_parser import APIParser, AmazonParser
from .eightfold_parser import EightfoldParser
from .smartrecruiters_parser import SmartRecruitersParser
from .rss_parser import RSSParser
from .graphql_parser import GraphQLParser, MetaParser
from .workday_parser import WorkdayParser, SalesforceParser
from .jibe_parser import JibeParser

__all__ = [
    'BaseJobParser',
    'ComeetParser',
    'GreenhouseParser',
    'APIParser',
    'AmazonParser',
    'EightfoldParser',
    'SmartRecruitersParser',
    'RSSParser',
    'GraphQLParser',
    'MetaParser',
    'WorkdayParser',
    'SalesforceParser',
    'JibeParser',
]
from .apple_parser import AppleParser

__all__.append('AppleParser')
from .microsoft_parser import MicrosoftParser

__all__.append('MicrosoftParser')
from .google_parser import GoogleParser

__all__.append('GoogleParser')

from .phenom_parser import PhenomParser

__all__.append('PhenomParser')

from .ashby_parser import AshbyParser

__all__.append('AshbyParser')
