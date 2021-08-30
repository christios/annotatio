# Annotatio

This repository contains the code for the annotation software that was developed in the scope of my Master's thesis which revolves around the standardization of orthography for Arabic dialects. This [link](https://drive.google.com/file/d/1VA4PZ1UKKQmpJXi0JYkh8miuOsNMDk-U/view?usp=sharing) takes you to the full thesis report, Chapter 3 of which contains all the information about this platform.

## Some Information
It was developed using *Flask* and *JavaScript*, and is in no way a final product since it still needs heavy tweaking.

It allows annotators to perform:
- Source-target pair segmentation
- Orthography standardization
- Morphological Segmentation
- Morphological (+ POS) tagging
- Spontaneous Orthography Tagging

## Running the App
To run the app, one must have a version of Python which is greater than 3.5, and the latest version of the Flask library. Simply run:

    python3 app.y

and open `127.0.0.1` on your browser. Sentences which are in the `annotatio/annotations/corpus` directory files will be saved to a file in `annotatio/annotations` named `annotations_$NAME.json` where `$NAME` is specified as the value of the `current_annotator` key in the `annotatio/config.json` file.