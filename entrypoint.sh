#!/bin/sh
python backup.py
(cd src && nikola build)
