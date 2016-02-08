echo "# Model, Target Length, Load time / s, Run time / s"
for f in uncompressed/*.bin;
do
    g=${f##uncompressed/};
    h=${g%.bin};

    for target in 1024 0;
    do
	    for n in `seq 1 10`;
	    do
		echo -n ${h} ${target}

		for t in `python spinnaker.py $f /dev/null $target | grep -o "[0-9.]\+ s$"`;
		do
			echo -n " ${t%s}"
		done

		echo
	    done
    done
done
