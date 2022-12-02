#!/bin/bash
po_dir=$(dirname "$(realpath "$0")")
pot_file="$po_dir"/yumex.pot
xgettext -f "$po_dir"/POTFILES -o $pot_file --add-comments=Translators --keyword=_ --keyword=C_1c,2 --from-code=UTF-8
sed -i "s/SOME DESCRIPTIVE TITLE./Yum Extender (yumex) POT file/" $pot_file
sed -i "s/YEAR THE PACKAGE'S COPYRIGHT HOLDER/$(date +%Y) Tim Lauridsen/" $pot_file
sed -i "s@same license as the PACKAGE package.@GNU GPLv3 license.@" $pot_file
sed -i "s/FIRST AUTHOR <EMAIL@ADDRESS>, YEAR./Tim Lauridsen, $(date +%Y)./" $pot_file

regex="$po_dir/([a-zA-Z_]*).po"
find "$po_dir" -type f -name "*.po" | sed -rn "s:$regex:\1:p" > "$po_dir/LINGUAS"
