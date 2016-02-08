for f in uncompressed/*.bin;
do
    g=${f##uncompressed/};
    python spinnaker.py $f compressed/oc_spinnaker_$g ;
done
