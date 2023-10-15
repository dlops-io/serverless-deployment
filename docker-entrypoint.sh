#!/bin/bash

echo "Container is running!!!"

if [ "${DEV}" = 1 ];
then
  pipenv shell
else
  pipenv run functions-framework --target translate_http
fi