from datetime import date, datetime
import os
import re
import statistics
import img2pdf
from PIL import Image

dirname = os.path.dirname(__file__)


if __name__ == "__main__":
    
    if not os.path.exists("./out"):
        os.mkdir("./out")
        
    if not os.path.exists("./temp"):
        os.mkdir("./temp")
        
    if not os.path.exists("./in"):
        os.mkdir("./in")
        print("Generated 'in' folder. Please use this for input.\nExiting")
        exit()
    
    now = datetime.now().strftime("%d%m%Y%H%M%S")
    
    temp = f"./temp/{now}"
    if not os.path.exists(temp):
        os.mkdir(temp)
        
    
    ins = []
    for fname in os.listdir("./in"):
            if not fname.endswith(".png"):
                continue
            path = os.path.join("./in", fname)
            if os.path.isdir(path):
                continue
            ins.append(path)
    
    for image in ins:
        loaded = Image.open(image).convert('RGBA')
        match = re.match(r'^\.\/in\\(.*)', image)
        image_name = match.group(1)
        
        width, height = loaded.size
        if width != 745:
            print(f"formatting incorrect for {image_name}, please ensure it is 745 x 1040 px\nIt will be skipped")
            continue
        if height != 1040:
            print(f"formatting incorrect for {image_name}, please ensure it is 745 x 1040 px\nIt will be skipped")
            continue

        pix = loaded.load()
        colourSample1 = pix[741, 1000]
        colourSample3 = pix[710, 1036]

        colourSample = (round(statistics.mean((colourSample1[0], colourSample3[0]))), 
                        round(statistics.mean((colourSample1[1], colourSample3[1]))), 
                        round(statistics.mean((colourSample1[2], colourSample3[2]))),
                        255)

        cardx, cardy = loaded.size
        
        xsize = cardx + 94
        ysize = cardy + 94

        BackgroundLayer = Image.new('RGBA', (xsize, ysize), colourSample)

        BackgroundLayer.paste(loaded, (round(xsize/2 - cardx/2), round(ysize/2 - cardy/2)), loaded)
        BackgroundLayer.save(f"{temp}/{image_name}")    
    
    out = []
    for fname in os.listdir(temp):
        if not fname.endswith(".png"):
            continue
        path = f"{temp}/{fname}"
        if os.path.isdir(path):
            continue
        out.append(path)

    with open(f"./out/{now}.pdf", "wb") as f:
        f.write(img2pdf.convert(out))

    print("Wrote sucessfully")
    exit()
    