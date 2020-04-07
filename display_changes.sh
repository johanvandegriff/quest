#!/bin/bash
file="$HOME/.quest/log.txt"
tail -f "$file"

exit
cd `dirname "$0"`

clear
while true
do
  TMPFILE=$(mktemp)
  cat "$file"
  cp "$file" "$TMPFILE"
  while diff "$file" "$TMPFILE" > /dev/null
  do
    sleep 0.5
  done
  clear
  echo "File $file last changed on:"
  date
  echo
done
