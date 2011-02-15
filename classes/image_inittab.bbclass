require conf/inittab.conf

IMAGE_PREPROCESS_INITTAB = ""
IMAGE_PREPROCESS_INITTAB_append_RECIPE_OPTION_inittab = "image_preprocess_inittab"
IMAGE_PREPROCESS_FUNCS += "${IMAGE_PREPROCESS_INITTAB}"

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
