require conf/fstab.conf

IMAGE_PREPROCESS_FSTAB = ""
IMAGE_PREPROCESS_FSTAB_append_RECIPE_OPTION_fstab = "image_preprocess_fstab"
IMAGE_PREPROCESS_FUNCS += "${IMAGE_PREPROCESS_FSTAB}"

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
