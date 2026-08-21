#!/bin/bash

sudo -u odoo odoo shell -d gp8 -c /etc/odoo/odoo.conf --no-http < "apps/main.py"
