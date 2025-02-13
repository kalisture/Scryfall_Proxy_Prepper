import json
from time import sleep
import requests
import tkinter as tk
from tkinter import *
from tkinter import ttk
from tkinter import scrolledtext
import re
import os
import img2pdf
from PIL import Image
import statistics
from io import BytesIO

#GUI setup
root = tk.Tk()
root.geometry("550x550")
root.title("Scryfall Proxy Prepper")

frame = tk.Frame(root)
frame.columnconfigure(0, weight=1)
frame.columnconfigure(1, weight=1)

deckNameLabel = tk.Label(root, text="Deck Name")
deckNameLabel.grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)

deckNameBox = tk.Entry(root, width=50)
deckNameBox.grid(row=0, column=1, padx=10, pady=10, sticky=tk.W)
deckNameBox.insert(0, "Commander Deck")

deckListLabel = tk.Label(root, text="Deck List")
deckListLabel.grid(row=1, column=0, padx=10, pady=10, sticky=tk.W+tk.N)

deckListBox = scrolledtext.ScrolledText(root, height=15, width=45)
deckListBox.grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)

isBleed = IntVar()
c1 = tk.Checkbutton(root, text='CosmoPrint Ready', variable=isBleed)
c1.grid(row=2, column=0, pady=10, padx=10, sticky=tk.W)

b1 = tk.Button(root, command=lambda: submit(), text="Submit")
b1.grid(row=3, column=0, pady=10, padx=30, sticky=tk.W)

progressbar = ttk.Progressbar()
progressbar.place(x=30, y=400, width=450)

progressbarLabel = tk.Label(root, text="")
progressbarLabel.place(x=30, y=430, width=450)

# Relative Directory
dirname = os.path.dirname(__file__)

#error flag
errored = False

def generate_directory_name(name, x=0):
    while True:
        dir_name = (name + (' ' + str(x) if x != 0 else '')).strip()
        if not os.path.exists(dir_name):
            os.mkdir(dir_name)
            return dir_name
        else:
            x = x + 1

def match_double(card_info):
    isDouble = card_info.find('//')
    if isDouble != -1:
        match = re.match(r'.*\((\w+)\)\s+(\w+-*\w*)', card_info)
        api_url = f"https://api.scryfall.com/cards/{match.group(1)}/{match.group(2)}"
        try:
            response = requests.get(api_url)
            if response.status_code == 200:
                data = response.json()
                sleep(0.1)
                if data['layout'] == 'transform':
                    return True
                return False
        except Exception as e:
            print(f"Error checking double face for {card_info}: {e}")
            errored = True
        return False
    return False

def download_image(card_info, save_dir, isBleed, face):
    global errored
    match = re.match(r'.*\((\w+)\)\s+(\w+-*\w*)', card_info)
    if match:
        amountR = re.match(r'(^\d+)', card_info)
        if amountR:
            amount = amountR.group(1)
        else:
            amount = 1
        set_code = match.group(1).lower()
        card_number = match.group(2)
        api_url = f"https://api.scryfall.com/cards/{set_code}/{card_number}?format=image&version=png&face={face}"
        try:    
            response = requests.get(api_url)
            if response.status_code == 200:
                
                if face == "back":
                    image_name = f"{set_code}_{card_number}_back.png"
                else:
                    image_name = f"{set_code}_{card_number}.png"
                

                if isBleed:
                    card = Image.open(BytesIO(response.content)).convert('RGBA')
                    pix = card.load()
                    colourSample1 = pix[741, 1000]
                    colourSample3 = pix[710, 1036]

                    colourSample = (round(statistics.mean((colourSample1[0], colourSample3[0]))), 
                                    round(statistics.mean((colourSample1[1], colourSample3[1]))), 
                                    round(statistics.mean((colourSample1[2], colourSample3[2]))),
                                    255)

                    cardx, cardy = card.size
                    
                    xsize = cardx + 94
                    ysize = cardy + 94

                    BackgroundLayer = Image.new('RGBA', (xsize, ysize), colourSample)

                    BackgroundLayer.paste(card, (round(xsize/2 - cardx/2), round(ysize/2 - cardy/2)), card)
                    
                    for i in range(1, int(amount) + 1):
                        if i != 1:
                            image_name = image_name.replace('.png', ('_' + str(i) + '.png'))
                        image_path = os.path.join(save_dir, image_name)
                        BackgroundLayer.save(image_path)
                
                else:
                    for i in range(1, int(amount) + 1):
                        if i != 1: 
                            image_name = image_name.replace('.png', ('_' + str(i) + '.png'))
                        image_path = os.path.join(save_dir, image_name)
                        with open(image_path, 'wb') as f:
                            f.write(response.content)
                print(f"Downloaded: {image_name}")

            else:
                with open(os.path.join(save_dir, "errors.txt"), 'a') as f:
                    f.write(f"Failed to download image for {card_info}. Status code: {response.status_code}\n")
                print(f"Failed to download image for {card_info}. Status code: {response.status_code}")
                errored = True

        except Exception as e:
            with open(os.path.join(save_dir, "errors.txt"), 'a') as f:
                f.write(f"Error downloading image for {card_info}: {e}\n")
            print(f"Error downloading image for {card_info}: {e}")
            errored = True
    else:
        with open(os.path.join(save_dir, "errors.txt"), 'a') as f:
            f.write(f"Invalid format for card: {card_info}\n")
        print(f"Invalid format for card: {card_info}")
        errored = True
        
def read_card_list(decklist):
    try:
        return [line.strip() for line in decklist if line.strip()]
    except FileNotFoundError:
        print(f"Card list file not found at. Please check the file path.")
        return []

def submit():
    deckList = deckListBox.get("1.0", tk.END).splitlines()
    deckName = deckNameBox.get()
    save_pointer = os.path.join(dirname, deckName)
    save_dir = generate_directory_name(save_pointer)
    doublesided_dir = save_dir + "/doublesided"
    cards = read_card_list(deckList)
    progressbar['maximum']=len(deckList)
    progressbarLabel['text']="Processing"
    c1.config(state="disabled")
    b1.config(state="disabled")
    global errored
    errored = False

    if not cards:
        print("No cards to process. Exiting.")
        return
    
    # Loop through each card in the list and download the image
    for card in cards:
        if match_double(card):
            os.makedirs(doublesided_dir, exist_ok=True)
            download_image(card, doublesided_dir, isBleed.get(), "front")
            download_image(card, doublesided_dir, isBleed.get(), "back")
        else:
            download_image(card, save_dir, isBleed.get(), "front")
        progressbar.step()
        root.update()
        sleep(0.1)
    progressbar.step(0.01)
    root.update()
    
    if isBleed.get():
        progressbar.config(mode="indeterminate")
        progressbar.start(10)
        progressbarLabel["text"]="Saving PDF's\nProgram may lag"
        root.update()
        imgs = []
        for fname in os.listdir(save_dir):
            if not fname.endswith(".png"):
                continue
            path = os.path.join(save_dir, fname)
            if os.path.isdir(path):
                continue
            imgs.append(path)
        with open(os.path.join(save_dir, deckName) + ".pdf", "wb") as f:
            f.write(img2pdf.convert(imgs))
            
        imgs = []
        if os.path.exists(doublesided_dir):
            for fname in os.listdir(doublesided_dir):
                if not fname.endswith(".png"):
                    continue
                path = os.path.join(doublesided_dir, fname)
                if os.path.isdir(path):
                    continue
                imgs.append(path)
            with open(os.path.join(doublesided_dir, deckName + "_doublesided") + ".pdf", "wb") as f:
                f.write(img2pdf.convert(imgs))
    
    for card in cards:
        with open(os.path.join(save_dir, "decklist") + ".txt", "a", encoding="utf-8") as f:
            f.write(card + "\n")
            
    if not errored:
        print(f"Process completed without errors\nSaved in {save_dir}")
        progressbarLabel['text']=f"Process completed without errors\nSaved in {save_dir}"
    else:
        progressbarLabel['text']=f"Process completed with recorded errors\nSaved in {save_dir}"
        print(f"Process completed with recorded errors\nSaved in {save_dir}")
    b1.config(state="active")
    c1.config(state="active")
    progressbar.stop()
    progressbar.config(mode="determinate")
    progressbar.step(0.01)
    root.update()

    
if __name__ == "__main__":
    root.mainloop()
