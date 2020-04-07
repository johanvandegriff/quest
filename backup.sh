#!/bin/bash
file=quest.py
backup=Backup

test -d "$backup" || mkdir "$backup"
touch "$backup/00000"
name=`ls "$backup" -1 | tail -1`
if diff -q "$backup/$name" "$file"
then
  echo "There are no changes since the last backup."
else
  name=`expr "$name" '+' '1'`
  name=`printf "%5s" "$name" | tr ' ' '0'`
  echo "$name"
  cp "$file" "$backup/$name"
fi
