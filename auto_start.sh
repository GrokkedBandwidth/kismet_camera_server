#!/bin/bash

LINE=$(sed '/START/q' constants.py | wc -l)
sed -i -e $LINE"s/False/True/" main.py

sleep 1

python3 main.py &

sleep 1

python3 http_request.py &