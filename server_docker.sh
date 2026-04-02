#! /bin/bash
clear
docker exec -it sbt_pars_server /bin/bash
python3 manage.py shell