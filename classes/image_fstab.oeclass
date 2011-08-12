require conf/fstab.conf

IMAGE_PREPROCESS_FUNCS:>USE_fstab = " image_preprocess_fstab"

image_preprocess_fstab () {
    if [ -e .${fstabfixupdir} ] ; then
        (
        cwd=`pwd`
        cd .${fstabfixupdir}
        for f in * ; do
            echo -e "\n# $f" >> $cwd${sysconfdir}/fstab
            cat $f >> $cwd${sysconfdir}/fstab
        done
        )
    fi
    rm -rf .${fstabfixupdir}
}
