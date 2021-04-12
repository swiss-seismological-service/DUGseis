#!/bin/bash

# Compare several files in the current directory
# with the corresponding ones of the reference directory.

# All tested files may contain less data than the reference files,
# so you can process just a part of the data.

reference_folder='/mnt/da/tmp/dug-seis/processing/00-reference'

echo 'Usage:'
echo "$0 xml                  Show names of differing XML files"
echo "$0 diff <filename>      Show diff of filename"
echo '============================================'


if [[ $1 == 'diff' ]]; then
    diff $2 $reference_folder/$2 | less
    exit
fi

echo 'Comparing trigger.csv:'
echo
diff <(cat trigger.csv | sort -n) <(cat $reference_folder/trigger.csv | sort -n) | egrep '^<'
echo
echo 'No output means: "test passed"'


echo '———————————————————————————————————————————–'
echo 'Comparing events.csv:'
echo
diff <(cat events.csv | sort -n) <(cat $reference_folder/events.csv | sort -n) | egrep '^<'
echo
echo 'No output means: "test passed"'


echo '———————————————————————————————————————————–'
echo 'Comparing event_loc.csv:'
echo
diff <(cat event_loc.csv | sort -n) <(cat $reference_folder/event_loc.csv | sort -n) | egrep '^<'
echo
echo 'No output means: "test passed"'


# QuakeML: compare all XML files in current directory
echo '———————————————————————————————————————————–'
echo 'Comparing QuakeML files:'
echo

nn=0
while read f
do
    # skip lines containing "eventParameters publicID"
    a=$(cat events/$f | grep -v '<eventParameters publicID=')
    b=$(cat $reference_folder/events/$f | grep -v '<eventParameters publicID=')
    if [[ $a != $b ]]; then
        ((nn=++nn))
        if [[ $1 == 'xml' ]]; then
            echo files $f differ
        fi
    fi
    # echo i = $i
done < <(find . -name "*xml" -exec basename {} \; | sort)

echo "$nn differing XML files in folder 'event'"
echo
echo 'No output means: "test passed"'
