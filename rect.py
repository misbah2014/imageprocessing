from PIL import Image

    # Download Image:

im = Image.open("Orignal.jpg")

    # Check Image Size
im_size = im.size
w,h = im.size
print ('w = {} , hight = {}'.format(w,h))

    # Define box inside image

left = w/2
top = h/2
width = 200
height = 200

    # Create Box

box = (left, top, left+width, top+height)

    # Crop Image

area = im.crop(box)
area.show()

    # Save Image

print (area.size)
#area.save("lena_selected_part.png", "PNG")