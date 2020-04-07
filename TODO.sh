#!/bin/bash
tmp=$(mktemp)
tmp2=$(mktemp)
awk='BEGIN{i=1}{printf("% 5d %s\n", i, $0);i++}'
sed='s/(^ *[0-9]*) */\1 /'
line='--------------------------------------------------------------------'
cat quest.py | awk "$awk" | grep '^ *[0-9]* *def' | sed -r "$sed" > "$tmp"
echo "$line" >> "$tmp"
cat quest.py | awk "$awk" | grep '^ *[0-9]*.*TODO' | sed -r 's/(^ *[0-9]*).*TODO/\1 TODO/' >> "$tmp"
echo "$line" >> "$tmp"
cat quest.py | awk "$awk" | grep '^ *[0-9]* *class' | sed -r "$sed" >> "$tmp"
while [[ ! -z "$1" ]]
do
#  cat "$tmp" | grep "^[0-9]* .*$1" > "$tmp2"
  cat "$tmp" | grep -i "$1\|$line" > "$tmp2"
  mv "$tmp2" "$tmp"
  shift
done
cat "$tmp"
rm "$tmp" "$tmp2" 2> /dev/null
