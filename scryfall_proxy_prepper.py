from time import sleep
import httpx
import requests
import tkinter as tk
import mtg_parser
from tkinter import *
from tkinter import ttk
from tkinter import scrolledtext
import re
import os
import img2pdf
from PIL import Image
import statistics
from io import BytesIO
from dotenv import load_dotenv

# GUI setup
root = tk.Tk()
root.geometry("550x600")
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
deckListLabel.grid(row=2, column=0, padx=10, pady=10, sticky=tk.W + tk.N)

deckListBox = scrolledtext.ScrolledText(root, height=15, width=45)
deckListBox.grid(row=2, column=1, padx=10, pady=10, sticky=tk.W)

deckURLLabel = tk.Label(root, text="Deck Url (Preferred)")
deckURLLabel.grid(row=1, column=0, padx=10, pady=10, sticky=tk.W + tk.N)

deckURLBox = tk.Entry(root, width=50)
deckURLBox.grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)

isBleed = IntVar()
c1 = tk.Checkbutton(root, text="CosmoPrint Ready", variable=isBleed)
c1.grid(row=3, column=1, pady=10, padx=10, sticky=tk.W)

b1 = tk.Button(root, command=lambda: submit(), text="Submit")
b1.grid(row=4, column=0, pady=10, padx=30, sticky=tk.W)

progressbar = ttk.Progressbar()
progressbar.place(x=30, y=450, width=450)

progressbarLabel = tk.Label(root, text="")
progressbarLabel.place(x=30, y=480, width=450)

# Relative Directory
dirname = os.path.dirname(__file__)

# error flag
errored = False


def generate_directory_name(name, x=0):
    while True:
        dir_name = (name + (" " + str(x) if x != 0 else "")).strip()
        if not os.path.exists(dir_name):
            os.mkdir(dir_name)
            return dir_name
        else:
            x = x + 1


def download_image(card_info, save_dir, isBleed):
    global errored
    match = re.match(r".*\((\w+)\)\s+(\w+-*\w*)", card_info)
    image_urls = []
    if match:
        amountR = re.match(r"(^\d+)", card_info)
        if amountR:
            amount = amountR.group(1)
        else:
            amount = 1
        set_code = match.group(1).lower()
        card_number = match.group(2)
        api_url = f"https://api.scryfall.com/cards/{set_code.upper()}/{card_number}"
        try:
            response = requests.get(api_url)
            if response.status_code == 200:
                data = response.json()
                sleep(0.1)
                if data["layout"] in ["transform", "modal_dfc", "double_faced_token"]:
                    image_urls.append(data["card_faces"][0]["image_uris"]["png"])
                    image_urls.append(data["card_faces"][1]["image_uris"]["png"])
                else:
                    image_urls.append(data["image_uris"]["png"])
        except Exception as e:
            print(f"Error searching for card info {card_info}: {e}")
            errored = True
        if not image_urls:
            with open(os.path.join(save_dir, "errors.txt"), "a") as f:
                f.write(f"Failed to find image URL for {card_info}.\n")
            print(f"Failed to find image URL for {card_info}.")
            errored = True
            return

        if len(image_urls) > 1:
            save_images(
                set_code,
                card_number,
                "front",
                image_urls[0],
                amount,
                save_dir + "/doublesided",
                isBleed,
            )
            save_images(
                set_code,
                card_number,
                "back",
                image_urls[1],
                amount,
                save_dir + "/doublesided",
                isBleed,
            )
        else:
            save_images(
                set_code, card_number, "front", image_urls[0], amount, save_dir, isBleed
            )
    return


def save_images(set_code, card_number, face, url, amount, save_dir, isBleed):
    global errored
    try:
        response = requests.get(url)
        if response.status_code == 200:

            if face == "back":
                image_name = f"{set_code}_{card_number}_back.png"
            else:
                image_name = f"{set_code}_{card_number}.png"

            if isBleed:
                card = Image.open(BytesIO(response.content)).convert("RGBA")
                pix = card.load()
                colourSample1 = pix[741, 1000]
                colourSample3 = pix[710, 1036]

                colourSample = (
                    round(statistics.mean((colourSample1[0], colourSample3[0]))),
                    round(statistics.mean((colourSample1[1], colourSample3[1]))),
                    round(statistics.mean((colourSample1[2], colourSample3[2]))),
                    255,
                )

                cardx, cardy = card.size

                xsize = cardx + 94
                ysize = cardy + 94

                BackgroundLayer = Image.new("RGBA", (xsize, ysize), colourSample)

                BackgroundLayer.paste(
                    card,
                    (round(xsize / 2 - cardx / 2), round(ysize / 2 - cardy / 2)),
                    card,
                )

                for i in range(1, int(amount) + 1):
                    image_path = os.path.join(
                        save_dir,
                        image_name.replace(set_code, (str(i) + "_" + set_code)),
                    )
                    BackgroundLayer.save(image_path)

            else:
                for i in range(1, int(amount) + 1):
                    image_path = os.path.join(
                        save_dir,
                        image_name.replace(set_code, (str(i) + "_" + set_code)),
                    )
                    BackgroundLayer.save(image_path)
                    with open(image_path, "wb") as f:
                        f.write(response.content)
            print(f"Printed: {image_name}")
    except Exception as e:
        with open(os.path.join(save_dir, "errors.txt"), "a") as f:
            f.write(
                f"Error downloading image for {card_number + " " + set_code}: {e}\n"
            )
        print(f"Error downloading image for {card_number + " " + set_code}: {e}")
        errored = True


def read_card_list(decklist):
    try:
        return [line.strip() for line in decklist if line.strip()]
    except FileNotFoundError:
        print(f"Card list file not found at. Please check the file path.")
        return []


def fetchDecklist(deck_url, deckList):
    load_dotenv()
    agent = os.getenv("USER_AGENT", "")
    headers = {"user-agent": agent}
    client = httpx.Client(headers=headers)
    cards = []
    try:
        result = mtg_parser.parse_deck(deck_url, http_client=client)
        for card in result:
            cards.append(
                f"{card.quantity} {card.name} ({card.extension}) {card.number}"
            )
    except Exception as e:
        print(
            f"Error fetching decklist from {deck_url}: {e}. You may not have a user-agent for Moxfield decklists"
        )
        cards = read_card_list(deckList)
    return cards


def submit():
    deckList = deckListBox.get("1.0", tk.END).splitlines()
    deckName = deckNameBox.get()
    if not os.path.exists(dirname + "/Decks"):
        os.mkdir(dirname + "/Decks")
    save_pointer = os.path.join(dirname + "/Decks", deckName)
    save_dir = generate_directory_name(save_pointer)
    doublesided_dir = save_dir + "/doublesided"
    if deckURLBox.get():
        cards = fetchDecklist(deckURLBox.get(), deckList)
    else:
        cards = read_card_list(deckList)
    progressbar["maximum"] = len(deckList)
    progressbarLabel["text"] = "Processing"
    c1.config(state="disabled")
    b1.config(state="disabled")
    global errored
    errored = False
    os.makedirs(doublesided_dir, exist_ok=True)

    if not cards:
        print("No cards to process.")
        progressbarLabel["text"] = "No cards to process."
    else:
        # Loop through each card in the list and download the image
        for card in cards:
            download_image(card, save_dir, isBleed.get())
            progressbar.step(1)
            root.update()
            sleep(0.1)
        root.update()

        if isBleed.get():
            progressbar.config(mode="indeterminate")
            progressbar.start(10)
            progressbarLabel["text"] = "Saving PDF's\nProgram may lag"
            root.update()
            imgs = []
            for fname in os.listdir(save_dir):
                if not fname.endswith(".png"):
                    continue
                path = os.path.join(save_dir, fname)
                if os.path.isdir(path):
                    continue
                imgs.append(path)
            if imgs:
                imgs.sort()
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
                if imgs:
                    imgs.sort()
                    with open(
                        os.path.join(doublesided_dir, deckName + "_doublesided")
                        + ".pdf",
                        "wb",
                    ) as f:
                        f.write(img2pdf.convert(imgs))

        for card in cards:
            with open(
                os.path.join(save_dir, "decklist") + ".txt", "a", encoding="utf-8"
            ) as f:
                f.write(card + "\n")

        if not errored:
            print(f"Process completed without errors\nSaved in {save_dir}")
            progressbarLabel["text"] = (
                f"Process completed without errors\nSaved in {save_dir}"
            )
        else:
            progressbarLabel["text"] = (
                f"Process completed with recorded errors\nSaved in {save_dir}"
            )
            print(f"Process completed with recorded errors\nSaved in {save_dir}")
    b1.config(state="active")
    c1.config(state="active")
    progressbar.stop()
    progressbar.config(mode="determinate")
    progressbar.step(0.01)
    root.update()


if __name__ == "__main__":
    root.mainloop()
