tool for creating bbox cutouts for letters or areas in the vesuvius challenge to be used as masks or otherwise.

![Screenshot 2024-01-05 at 8 38 09 AM](https://github.com/bruniss/letter_label/assets/120566210/9ae42ef4-755f-49e4-9fce-ce86a9581db4)


download the zip, or clone it. cd into the repo and open it with bbox_gui.py

pan by click + drag,
zoom with scroll wheel,
create a bbox with 'c' and then click and drag, then name your bbox

no current method for rotation, non-regtangular boxes, or deletion/modification as these are just a tad complicated for me right now.

when you are done making them, click the cutout bboxes at the bottom of the window, and it will cut out the inklabels, mask, and layers tifs for each bbox region, along with a coco, cvat, and basic text file locations and descriptions for all of the bboxes, and a progress image, that looks like this:

![bbox_progress](https://github.com/bruniss/letter_label/assets/120566210/d0447c6b-36cb-4420-82e7-e86050dc96b1)
