from datetime import datetime
from .fields import EbirdFields
import re

regex_filter = r"\([^)]*\)"

datetime_format = "%Y-%m-%d %H:%M"
date_format = "%Y-%m-%d"


class Observation(object):
    def __init__(self, observation):
        self.observation_date = observation[EbirdFields.observation_date][0:10]
        if len(observation[EbirdFields.observation_date]) > 10:
            self.observation_datetime = datetime.strptime(observation[EbirdFields.observation_date], datetime_format)
        else:
            self.observation_datetime = datetime.strptime(observation[EbirdFields.observation_date], date_format)
        self.location = re.sub(regex_filter, "", observation[EbirdFields.location_name]).split(",")[0][0:55]
        self.name = re.sub(regex_filter, "", observation[EbirdFields.common_name])
        self.subname = observation[EbirdFields.sub_subnational_name]
