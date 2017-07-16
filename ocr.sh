#!/bin/bash
# Script runs optical character recognition with tesseract

SCRIPT=`realpath -s $0`
ROOT=`dirname $SCRIPT`
IMGS=$ROOT"/imgs/"
TMP=$ROOT"/tmp/"
# get current scan
IMGID=`ls $ROOT/tmp/dst_*.jpg 2>/dev/null | awk -F'_' '{print $2}' | awk -F'.' '{print $1}'`
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
PREPID=$(hexdump -v -e '/1 "%02X"' -e '/8 "\n"' $IMGS"IMG_"$IMGID".JPG" \
             | tail -n 5 | head -n 1 | tr -d '[:space:]')
PREPD=$PREP$PREPID".png"
if [ ! -f $PREPD ]; then
    cp $TMP"original.jpg" $PREP$PREPID"_"$IMGID".jpg"
    cp $DST $PREP"dst_"$IMGID".jpg"
    echo "Preprocessing to $PREPD"
    # text clean the image
    convert -units PixelsPerInch -respect-parenthesis \
            \( $DST -colorspace gray -type grayscale -contrast-stretch 0 \) \
            \( -clone 0 -negate -lat 30x30+5% \) \
            -compose copy_opacity -composite -fill white -opaque none \
            -alpha off -background white -deskew 40% -sharpen 0x4.0 \
            -white-threshold 99.9% -trim -density 350 +repage \
            $PREPD
    chmod 666 $PREPD
else
    echo "Already preprocessed: $PREPD"
fi;
# create directory for saving ocr txt
mkdir -p $ROOT/txt
TXTD=$ROOT"/txt/"
TXTF=$TXTD$(hexdump -v -e '/1 "%02X"' -e '/8 "\n"' $IMGS"IMG_"$IMGID".JPG" \
                | tail -n 5 | head -n 1 | tr -d '[:space:]')
tesseract -l deu+eng $PREPD $TXTF
