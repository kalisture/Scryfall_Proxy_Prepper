# Scryfall_Proxy_Prepper
Requirements:
Python 3, Pip

Installation:
Run install requirements.bat

Running:
python ./scryfall_proxy_prepper.py

OR

run.bat

-----------------------------------------------------------------------------------------------------
Usage:
Defualt export format for best results. Set code and Collection number mandatory. e.g.:

1 Cut Down (DMU) 89
1 Sheoldred, the Apocalypse (DMU) 107

-----------------------------------------------------------------------------------------------------
Notes:
By default will download images, taking into account printings, amount of copies.

Deck will never overwrite, will create a new folder.

Double sided cards will be stored seperately.

x CosmoPrint Ready - Adds a 3+mm bleed, and converts to PDF at the end.

When providing to me, please specify what card back you want (None, Default, Custom (Provided))

-----------------------------------------------------------------------------------------------------

custom_pdf.py lets you turn downloaded images (normal), adds the bleed and creates a pdf ready to proxy.

Place images in the in folder
