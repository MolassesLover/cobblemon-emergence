#!/usr/local/bin/env sh

mkdir build

cp -r packs/resourcepack build/emergence-resources
cp -r packs/datapack build/emergence-data

mkdir -p build/emergence-resources/licenses
cp docs/licenses/LGPL3.md build/emergence-resources/LGPL3.md

cd build/emergence-resources
zip ../emergence-resources.zip *

cd ../emergence-data
zip ../emergence-data.zip *

cd ../../

sha1sum build/emergence-resources.zip > build/emergence-resources.zip.sha1
sha1sum build/emergence-data.zip > build/emergence-data.zip.sha1