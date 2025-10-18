#!/bin/bash

if [ -z "$1" ]; then
  echo "Utilisation: $0 chemin/vers/fichier.sql"
  exit 1
fi

FILE=$1

if [ ! -f "$FILE" ]; then
  echo "Le fichier '$FILE' est introuvable."
  exit 1
fi

docker exec -i ais-db psql -U postgres -d ais < "$FILE"
