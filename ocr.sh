#!/bin/bash
# Script runs optical character recognition with tesseract

SCRIPT=`realpath -s $0`
ROOT=`dirname $SCRIPT`
IMGS=$ROOT"/imgs/"
TMP=$ROOT"/tmp/"
# get current scan
IMGID=`ls tmp/dst_*.jpg 2>/dev/null | awk -F'_' '{print $2}' | awk -F'.' '{print $1}'`
DST=$TMP'dst_'$IMGID'.jpg'
if [ -f $DST ]; then
    echo "Using scan       $DST"
else
    echo "Scan not found..."
    echo "Run 'python scanner.py IMG_XXXX.JPG' first"
    exit 1
fi;
# create directory for saving enhanced image
mkdir -p $ROOT/prp
PREP=$ROOT"/prp/"
PREPD=$PREP$(hexdump -n 8 -v -e '/1 "%02X"' -e '/8 "\n"' \
                     $IMGS/IMG_$IMGID.JPG)".png"
if [ ! -f $PREPD ]; then
    echo "Preprocessing to $PREPD"
    convert -auto-level -sharpen 0x4.0 -contrast $DST \
            -depth 300 -units PixelsPerInch -resample 300 $PREPD
else
    echo "Already preprocessed: $PREPD"
fi;
# create directory for saving ocr txt
mkdir -p $ROOT/txt
TXTD=$ROOT"/txt/"
TXTF=$TXTD$(hexdump -n 8 -v -e '/1 "%02X"' -e '/8 "\n"' \
                    $IMGS/IMG_$IMGID.JPG)
tesseract -l deu $DST $TXTF
