#!/bin/bash
file="quest.py"
release="Release"
remotedir="johanadmin@vandegriff.net:johan.vandegriff.net/quest/"


test -d "$release" || mkdir "$release"
lastFile="$release/.last-release"
last=".last-release"
test -f "$lastFile" || echo -n "$last" > "$lastFile"
last="$release/"`cat "$lastFile"`

if diff -q "$last" "$file"
then
  echo "There are no changes since the last release."
else
  version="$1"
  test -z "$version" && echo "Enter the version as the 1st argument." && exit 1
  extension="${file##*.}"                     # get the extension
  filename="${file%.*}"                       # get the filename
  name="${filename}-${version}.$extension"
  zipname="${filename}-${version}.zip"
  path="$release/$name"
  zippath="$release/$zipname"
  test -f "$path" && echo "$path already exists!" && exit 1
  cp "$file" "$path" &&
  (cd "$release" && zip "$zipname" "$name" -9) &&
  scp "$zippath" "$remotedir" &&
  echo -n "$name" > "$lastFile" &&
  echo -e '\033[92m'"$file version $version succesfully released."'\033[0m'
  #green text

fi
