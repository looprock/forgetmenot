#!/bin/sh
curl -X POST -H "Content-Type: application/x-www-form-urlencoded" -d @data.txt http://localhost:18080/todo
