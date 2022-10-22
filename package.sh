#!/bin/bash

mkdir package
mkdir package/plugins
cp -r teardrops/* package/plugins
mkdir package/resources
cp teardrops/teardrops.png package/resources/icon.png
cp metadata.json package
cd package
zip -r ../package.zip .
cd ..