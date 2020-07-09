
from PIL import Image

if __name__ == "__main__":
    loop = True

    input_loc = 'Orignal.jpg'
    output_loc = 'cropped.jpg'
    im = Image.open("Orignal.jpg")
    im_size = im.size
    w, h = im.size
    width = 240
    height = 420
    left = (w / 2) - (width/2)
    top = (h / 2) - (height/2)

    box = (left, top, left + width, top + height)
    area = im.crop(box)
    area.show()
    print(area.size)
    area.save("cropped.jpg", "JPEG")

