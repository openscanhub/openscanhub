#!/usr/bin/env bash

SELF="$0"

die()
{
    echo -e "usage:\n$SELF <RHEL_VERSION> <RHEL_RELEASE>\n"
    echo "$SELF: error: $1" >&2
    exit 1
}

isnumber() 
{ 
    test "$1" && printf '%d' "$1" &>/dev/null; 
}

OUT_PATH="/etc/mock/"
RHEL_VERSION="$1"
isnumber $RHEL_VERSION || die "Incorrect version number."
RHEL_RELEASE="$2"
[[ "$RHEL_RELEASE" =~ ^[0-9a-zA-Z\,\.]+$ ]] || die "Incorrect release string."
#isnumber $RHEL_RELEASE || die "Incorrect release number."

TAGS=( RHEL-$RHEL_VERSION.$RHEL_RELEASE RHEL-$RHEL_VERSION.$RHEL_RELEASE-build RHEL-$RHEL_VERSION.$RHEL_RELEASE-candidate RHEL-$RHEL_VERSION.$RHEL_RELEASE-override RHEL-$RHEL_VERSION.$RHEL_RELEASE-test );
TAGS+=( dist-${RHEL_VERSION}E-U${RHEL_RELEASE} dist-${RHEL_VERSION}E-U${RHEL_RELEASE}-build dist-${RHEL_VERSION}E-U${RHEL_RELEASE}-fastrack dist-${RHEL_VERSION}E-U${RHEL_RELEASE}-fastrack-build dist-${RHEL_VERSION}E-U${RHEL_RELEASE}-pending dist-${RHEL_VERSION}E-Client-U${RHEL_RELEASE} dist-${RHEL_VERSION}E-Server-U${RHEL_RELEASE} dist-${RHEL_VERSION}E-extras-U${RHEL_RELEASE} dist-${RHEL_VERSION}E-extras-U${RHEL_RELEASE}-pending)

# DEBUG
#TAGS=( RHEL-$RHEL_VERSION.$RHEL_RELEASE-build )

for tag in "${TAGS[@]}" ; do
    brew mock-config "coverity/$tag" --tag $tag --arch=x86_64 -o "tmp_${tag}.cfg" &>/dev/null;
    [ $? -eq "0" ] && sed 's/\\n/\n/g' <tmp_${tag}.cfg >${tag}.cfg && rm "tmp_${tag}.cfg";
done    

