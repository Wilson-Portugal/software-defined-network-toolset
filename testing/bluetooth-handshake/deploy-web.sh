#!/bin/bash

# Target remote details
CREDENTIALS=`cat production-credentials.txt | head -n 1`
FTP_HOST=`echo $CREDENTIALS | cut -d '|' -f 1`
FTP_USER=`echo $CREDENTIALS | cut -d '|' -f 2`
FTP_PASS=`echo $CREDENTIALS | cut -d '|' -f 3`
REMOTE_DIR="/public_html/bluetooth-handshake" 

LOCAL_DIR="/mnt/chromeos/MyFiles/software-defined-network-toolset/testing/bluetooth-handshake"

# ---------------------------------------------------------------
# NEW: Stage the freshly compiled index2.html into index.html
# ---------------------------------------------------------------
# if [ -f "$LOCAL_DIR/index2.html" ]; then
#     echo "Staging: Copying fresh index2.html to index.html..."
#     cp "$LOCAL_DIR/index2.html" "$LOCAL_DIR/index.html"
# else
#     echo "WARNING: index2.html not found! Deploying existing index.html."
# fi
# ---------------------------------------------------------------

# 1. Read current build number, default to 1 if missing
VERSION_FILE="$LOCAL_DIR/build-number.txt"

if [ ! -f $VERSION_FILE ]; then
    echo "1.0.0" > "$VERSION_FILE"
fi

MAJOR=$(cut -d '.' -f 1 "$VERSION_FILE")
MINOR=$(cut -d '.' -f 2 "$VERSION_FILE")
RELEASE=$(cut -d '.' -f 3 "$VERSION_FILE")

CURRENT_BUILD="$MAJOR.$MINOR.$RELEASE"

# Increment the patch integer
RELEASE=$((RELEASE + 1))
NEXT_BUILD="$MAJOR.$MINOR.$RELEASE"

echo "Current Build: $CURRENT_BUILD -> Incremented to Build: $NEXT_BUILD"

# 2. Update the tracking text file immediately
echo "$NEXT_BUILD" > "$VERSION_FILE"

# 3. Stream the template into a live sw.js, replacing the version token
sed "s/%%BUILD_VERSION%%/$NEXT_BUILD/g" "$LOCAL_DIR/sw.js.template" > "$LOCAL_DIR/sw.js"
sed "s/%%BUILD_VERSION%%/$NEXT_BUILD/g" "$LOCAL_DIR/index2.html" > "$LOCAL_DIR/index.html"
# -----------------------------------------------

# HUMAN-READABLE MANIFEST CHECKLIST
echo "Deploying PWA frontend assets to $FTP_HOST..."

# Explicit line-by-line file transmission
lftp <<EOF
set ssl:verify-certificate no
set ftp:ssl-allow yes 
open -u "$FTP_USER","$FTP_PASS" "$FTP_HOST"
cd $REMOTE_DIR
put $LOCAL_DIR/index.html
put $LOCAL_DIR/sw.js
put $LOCAL_DIR/manifest.json
put $LOCAL_DIR/favicon.ico
put $LOCAL_DIR/sgn-radio-512x512.png
put $LOCAL_DIR/sgn-radio.svg
bye
EOF

echo "Web deployment complete! System tracking is now at build v$NEXT_BUILD."
