#Visual Description of textual Instructions
------------------------------

What is it?
------------------------------

This is based on the motivation that images along with text are more comprehensive than text alone.
User first provides a query like 'How to make coffee' along with a set of instructions on the UI hosted locally.
Model then analyzes the text and associates relevant images with it, setting everything into a proper template. Images are fetched in an online fashion using Google API. The model is not domain-specific; user can specify any set of instructions.

Database
------------------------------

No state of the art model exists. So model has no figures to compare with. Our model uses wikihow as the ground truth for comparison of results. (`wikihow_final.py` is highly dependent on how classes are defined in the html page.)

Pre-requisites
------------------------------
User needs to make sure following packages are present in his/her python environment.

Packages : [flask, os, pprint, googleapiclient,re, nltk, codecs, pickle, opencv, PIL, numpy, math, scipy, operator, matplotlib, django]

Stanford coreNLP:

1. Download the coreNLP from 'http://stanfordnlp.github.io/CoreNLP/
2. If files: `stanford-parser.jar`, `stanford-parser-3.4.1-models.jar` are not present in the directory where Stanford CoreNLP is            installed, download them (directly by searching their name in google) to directory where Stanford CoreNLP is installed.



How to run the model?
------------------------------

Run the code from command-propmt. Goto the loaction in cmd where all the codes are present. The code runs in a three-way manner:

1. User first needs to run the index.py on command-prompt that hosts the UI on local server which user can access through port number `5000`. Type `http://localhost:5000/` in your web-browser.
2. On the hosted UI, user then needs to fetch the `Query` and corresponding instruction-set(`Description`). This automatically runs the `prototype.py` which does all sorts of text-processing and stores the variables, images in directories that have paths under variable-name 'newpath. Change it as per your convenience.
3. For the time-being, user has to run prototype2.py manually using command-prompt after step2.
    Type `python prototype2.py`.
    prototype2.py does all sorts of image-processing and finally displays a single image which contains instruction-set along with their images.

Note: Representative image for each entity is selected manually, After step-2, user needs to navigate to image_directory of every entity and number the representative image as `{entity_name}_1.jpg`.

Text-processing
------------------------------
Every instruction is fed to Stanford dependecy parser which builts a dependency tree(list) out of it. Items in the returned list have the following syntax : `[((head,head_tag),relation,(dependent,dependent_tag))]`. Based on the relation, model identifies head action verb and its dependent modifiers to form main_queries and their tags. It then fetches them to Google API and retrives images.

Image-processing
------------------------------
For the time-being, user has to maually set representative image for every entity. Coherency is ensured using Image histogram-matching which builds histogram of each image on all the 3 channels with 8-bins each. It then computes the distance between the histograms using 'Correlation' method(User can specify his/her own method in `prototype2.py`) and returns a score. Based on the score,most coherent image is chosen and coherency is ensured. 


