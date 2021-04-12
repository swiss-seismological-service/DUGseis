#  Celery App
#
# :copyright:
#    ETH Zurich, Switzerland
# :license:
#    GNU Lesser General Public License, Version 3
#    (https://www.gnu.org/copyleft/lesser.html)
#
# -*- coding: utf-8 -*-

# Broker settings.
broker_url = "redis://"
# Using the database to store task state and results.
result_backend = "redis://"

# List of modules to import when celery starts.
imports = (
    "dug_seis.processing.celery_tasks"
)

accept_content = ["pickle"]
task_serializer = "pickle"
result_serializer = "pickle"
task_ignore_result = False
