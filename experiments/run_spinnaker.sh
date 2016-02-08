for f in uncompressed/*.bin;
do
    g=${f##uncompressed/};
    python spinnaker.py $f compressed/oc_spinnaker_$g ;
    python spinnaker.py $f /dev/null --memory-profile memory_profiles/$g ;
done
