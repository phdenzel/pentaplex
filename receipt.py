#!/usr/bin/env python

import uuid

print uuid.uuid5(uuid.NAMESPACE_DNS, "test")
