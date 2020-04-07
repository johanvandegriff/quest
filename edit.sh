#!/bin/bash
# Create a temporary file
TMPFILE=$(mktemp)

# Add stuff to the temporary file
echo "rm -f $TMPFILE" >> $TMPFILE
echo "source ~/.bashrc" > $TMPFILE
echo "alias 'edit=nano quest.py'" >> $TMPFILE
echo "edit" >> $TMPFILE

# Start the new bash shell
bash --rcfile $TMPFILE
