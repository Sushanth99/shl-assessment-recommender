#!/usr/bin/env python
from typing import Union
import re

def has_url(query: str) -> Union[str, None]:
    regex_url = r"((http|https)\:\/\/)[a-zA-Z0-9\.\/\?\:@\-_=#]+\.([a-zA-Z]){2,6}([a-zA-Z0-9\.\&\/\?\:@\-_=#])*"
    match = re.search(regex_url, query)
    return match.group(0) if match else None