# for f in uncompressed/*.bin;
# do
#     g=${f##uncompressed/};
#     echo $g ;
#     python mtrie.py $f compressed/mtrie_$g > /dev/null &
#     python remove_default_routes.py $f compressed/remove_default_$g > /dev/null &
#     python espresso.py $f compressed/esp_tables_no_offset_$g --whole-table --no-off-set --remove-default-entries > /dev/null ;
# done

for f in uncompressed/*.bin;
do
    g=${f##uncompressed/};
    python espresso.py $f compressed/esp_subtables_full_$g ;
done
