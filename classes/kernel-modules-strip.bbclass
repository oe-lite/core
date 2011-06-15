# -*- mode:python; -*-

KERNEL_MODULES_FIXUP_FUNCS ?= "kernel_modules_strip"
FIXUP_FUNCS += "${KERNEL_MODULES_FIXUP_FUNCS}"

kernel_modules_strip () {
    if [ -e lib/modules ] ; then
        modules=`find lib/modules -name \*.ko`
        if [ -n "$modules" ]; then
            for module in $modules ; do
                if ! [ -d "$module"  ] ; then
                    ${STRIP} -v -g $module
                fi
            done    
        fi
    fi
}
