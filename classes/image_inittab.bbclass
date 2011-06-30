require conf/inittab.conf

IMAGE_PREPROCESS_FUNCS += "image_preprocess_inittab"

image_preprocess_inittab () {
    if [ -e .${inittabfixupdir} ] ; then
        (
        cwd=`pwd`
        cd .${inittabfixupdir}
        for f in * ; do
            echo -e "\n# $f" >> $cwd${sysconfdir}/inittab
            cat $f >> $cwd${sysconfdir}/inittab
        done
        )
    fi
    rm -rf .${inittabfixupdir}
}
