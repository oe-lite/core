#!/bin/sh
UBI_VOL=0
SERVICE_MODE=0

ROOT_MOUNT=/rootfs

early_setup() {
    mkdir /proc
    mkdir /sys
    mkdir /tmp
    mount -t proc proc /proc
    mount -t sysfs sysfs /sys
    mount -t tmpfs tmpfs /tmp
    echo 255 > /sys/class/leds/led3:green:os/brightness
    mdev -s
    echo /bin/mdev >/proc/sys/kernel/hotplug
}

undo_setup() {
    umount /tmp
    umount /sys
    umount /proc
    rm -r /proc
    rm -r /sys
    rm -r /tmp
}

read_args() {
    [ -z "$CMDLINE" ] && CMDLINE=`cat /proc/cmdline`
    for arg in $CMDLINE; do
        optarg=`expr "x$arg" : 'x[^=]*=\(.*\)'`
        case $arg in
            rootfstype=*)
                ROOT_FSTYPE=$optarg ;;
            mtdnr=*)
                MTD=$optarg ;;
            ubivol=*)
                UBI_VOL=$optarg ;;
            servicemode=*)
                SERVICE_MODE=$optarg ;;
        esac
    done
}

mount_root() {
    ubiattach /dev/ubi_ctrl -m $MTD -d 0 || \
	fatal "Error attach MTD device $MTD to UBI"

    if [ -f /sys/devices/virtual/ubi/ubi0/ubi0_${UBI_VOL}/name ]; then
	[ -d $ROOT_MOUNT ] || mkdir $ROOT_MOUNT
	mount -t ubifs ubi0_${UBI_VOL} $ROOT_MOUNT || \
	    fatal "Error mounting UBI volume $UBI_VOL (mtd $MTD)"
    else
	fatal "Error finding UBI volume $UBI_VOL on mtd $MTD"
    fi
    [ -x $ROOT_MOUNT/sbin/init ] || fatal "No /sbin/init in root filesystem"
}


boot_root() {
    cd $ROOT_MOUNT
    exec busybox switch_root $ROOT_MOUNT /sbin/init
}

fatal() {
    echo $1
    echo
    undo_setup
    exec /sbin/init
}

get_mtd() {
    for i in 0 1 2 3 4 5 6 7 8 9;
    do
	MTD=$i
	[ -d "/sys/class/mtd/mtd${MTD}" ] && \
	    [ `cat /sys/class/mtd/mtd${MTD}/name` = "$1" ] && return
    done
    echo "Error: mtd device with name $1, not found"
    return 1
}

service_mode() {
    echo

    if [ "$SERVICE_MODE" -eq "1" ];
    then
	:
#    elif read -p "Press Enter to activate service mode" -t 3;
#    then
#	:
    else
	return
    fi
    
    echo Entering service mode...
    undo_setup
    exec /sbin/init
}

early_setup

MTD=""
get_mtd "rootfs"

read_args
service_mode
mount_root
undo_setup
boot_root
