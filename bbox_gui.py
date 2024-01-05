
import os
import random
import tkinter as tk
from tkinter import filedialog, simpledialog, ttk
from PIL import Image, ImageTk, ImageDraw
import json

Image.MAX_IMAGE_PIXELS = None

class App:
    def __init__(self, root):

        self.selected_bbox_index = None  # To keep track of the selected bounding box

        self.root = root
        self.root.title("Bounding Box Application")
        self.root.geometry("1024x1024")  # Set initial window size
        self.open_segment_btn = tk.Button(root, text="Open Segment", command=self.open_segment)
        self.open_segment_btn.pack()
        self.canvas = tk.Canvas(root, bg='white')
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<MouseWheel>", self.zoom)
        self.mode = "pan"  # Default mode is panning
        self.root.bind("<c>", lambda e: self.set_mode("bbox_creation"))
        self.root.bind("<Escape>", lambda e: self.set_mode("pan"))  # Escape key to return to panning mode
        self.canvas.bind("<Button-1>", self.handle_canvas_click)
        self.root.bind("<Delete>", self.on_delete_press)

        self.rect = None
        self.start_x = None
        self.start_y = None
        self.bounding_boxes = []
        self.folder_path = None
        self.current_bbox_name = None
        self.image_id = None
        self.img = None
        self.tk_img = None
        self.scale = 1.0
        self.orig_img_width = None
        self.orig_img_height = None
        self.selected_bbox_index = None

        self.mode = "pan"  # Default mode is panning

        self.cut_bboxes_btn = tk.Button(root, text="Cut BBoxes", command=self.cut_bboxes)
        self.cut_bboxes_btn.pack(side=tk.LEFT)

        self.progress = ttk.Progressbar(root, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress.pack(side=tk.BOTTOM)

        self.mode = "pan"  # Default mode is panning
        self.enable_pan()  # Enable panning at startup


    def set_mode(self, mode):
        self.mode = mode
        print("Mode set to:", mode)
        if mode == "bbox_creation":
            self.canvas.bind("<ButtonPress-1>", self.on_button_press)
            self.canvas.bind("<B1-Motion>", self.on_move_press)
            self.canvas.bind("<ButtonRelease-1>", self.finish_bbox_creation)
        elif mode == "pan":
            self.enable_pan()

    def handle_canvas_click(self, event):
        if self.mode == "pan":
            self.start_pan(event)
        elif self.mode == "bbox_creation":
            # bbox creation logic here
            pass
        else:  # Handle selection in other modes
            self.select_bbox(event)
    
    def on_canvas_click(self, event):
        # Re-bind the panning function if it's not a bounding box creation mode
        if not hasattr(self, 'bbox_creation_mode') or not self.bbox_creation_mode:
            self.enable_pan()

        click_x, click_y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        print("Canvas clicked at:", click_x, click_y)  # Debugging statement

        self.selected_bbox_index = None
        for index, (_, coords, rect_id) in enumerate(self.bounding_boxes):
            x1, y1, x2, y2 = [coord * self.scale for coord in coords]
            if x1 <= click_x <= x2 and y1 <= click_y <= y2:
                self.selected_bbox_index = index
                print("Selected bounding box:", index)  # Debugging statement
                self.canvas.itemconfig(rect_id, outline='blue')  # Highlight
            else:
                self.canvas.itemconfig(rect_id, outline='red')  # Reset others

    def enable_pan(self):
        self.canvas.bind("<ButtonPress-1>", self.start_pan)
        self.canvas.bind("<B1-Motion>", self.on_pan)

    def on_delete_press(self, event):
        if self.selected_bbox_index is not None:
            _, _, rect_id = self.bounding_boxes.pop(self.selected_bbox_index)
            self.canvas.delete(rect_id)
            self.selected_bbox_index = None

    def open_segment(self):
        self.folder_path = filedialog.askdirectory(title="Select a Segment Folder")
        if not self.folder_path:
            return

        if not self.verify_segment_folder(self.folder_path):
            print("Segment folder verification failed.")
            return

        self.display_image(os.path.join(self.folder_path, "inklabels.png"))

    def start_bbox_creation(self, event):
        # Start bbox creation and revert back to panning after one bbox is created
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.finish_bbox_creation)

    def finish_bbox_creation(self, event):
        if self.rect:
            self.current_bbox_name = simpledialog.askstring("Bounding Box Name", "Enter a name for this bounding box:")
            if self.current_bbox_name:
                bbox_coords = self.canvas.coords(self.rect)
                scaled_bbox_coords = [coord / self.scale for coord in bbox_coords]  # Scale down to original image size
                self.bounding_boxes.append((self.current_bbox_name, scaled_bbox_coords, self.rect))  # Store rect ID
                self.rect = None
            self.enable_pan()

    def select_bbox(self, event):
        click_x, click_y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        for index, (_, bbox_coords, rect_id) in enumerate(self.bounding_boxes):
            x1, y1, x2, y2 = [c * self.scale for c in bbox_coords]
            if x1 <= click_x <= x2 and y1 <= click_y <= y2:
                self.selected_bbox_index = index
                self.canvas.itemconfig(rect_id, outline='blue')  # Highlight selected bbox
                return
        self.selected_bbox_index = None  # Deselect if no bbox is clicked

    def enable_pan(self):
        self.canvas.bind("<ButtonPress-1>", self.start_pan)
        self.canvas.bind("<B1-Motion>", self.on_pan)
    
    def on_pan(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def start_pan(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def zoom(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        factor = 1.1 if event.delta > 0 else 0.9
        self.scale *= factor

        new_width = int(self.orig_img_width * self.scale)
        new_height = int(self.orig_img_height * self.scale)
        resized_img = self.img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.tk_img = ImageTk.PhotoImage(resized_img)
        self.canvas.itemconfig(self.image_id, image=self.tk_img)

        # Update the position of the bounding boxes
        for name, original_coords, rect_id in self.bounding_boxes:
            scaled_coords = [coord * self.scale for coord in original_coords]
            self.canvas.coords(rect_id, *scaled_coords)  # Update using rect ID

        self.canvas.configure(scrollregion=self.canvas.bbox("all"))


    def verify_segment_folder(self, folder_path):
        required_files = ['mask.png', 'inklabels.png']
        required_folder = 'layers'

        for file in required_files:
            if not os.path.exists(os.path.join(folder_path, file)):
                print(f"Missing file: {file}")
                return False

        layers_path = os.path.join(folder_path, required_folder)
        if not os.path.exists(layers_path) or not os.listdir(layers_path)[:10]:
            print("Missing or incomplete layers folder.")
            return False

        return True

    def display_image(self, image_path):
        self.img = Image.open(image_path)
        self.orig_img_width, self.orig_img_height = self.img.size
        self.tk_img = ImageTk.PhotoImage(self.img)
        self.image_id = self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)
        self.canvas.after(100, self.reset_zoom)  # Delay the reset_zoom call to ensure canvas size is updated

    def on_button_press(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        if not self.rect:
            self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, 1, 1, outline='red')

    
    def reset_zoom(self):
        self.scale = 1.0
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        scale_width = canvas_width / self.orig_img_width
        scale_height = canvas_height / self.orig_img_height
        self.scale = min(scale_width, scale_height, 1)
        resized_img = self.img.resize((int(self.orig_img_width * self.scale), int(self.orig_img_height * self.scale)), ImageResampling.LANCZOS)
        self.tk_img = ImageTk.PhotoImage(resized_img)
        self.canvas.itemconfig(self.image_id, image=self.tk_img)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def on_move_press(self, event):
        curX, curY = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
        self.canvas.coords(self.rect, self.start_x, self.start_y, curX, curY)

    def on_button_release(self, event):
        if self.rect:
            self.current_bbox_name = simpledialog.askstring("Bounding Box Name", "Enter a name for this bounding box:")
            if self.current_bbox_name:
                bbox_coords = self.canvas.coords(self.rect)
                self.bounding_boxes.append((self.current_bbox_name, bbox_coords))
                self.rect = None

    

        
    def cut_bboxes(self):

        output_dir = filedialog.askdirectory(title="Select Output Folder")
        if not output_dir:  # User cancelled the dialog
            return
        
        inklabels_img = Image.open(os.path.join(self.folder_path, "inklabels.png"))
        mask_img = Image.open(os.path.join(self.folder_path, "mask.png"))

        # Create a transparent overlay
        bbox_overlay = Image.new("RGBA", inklabels_img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(bbox_overlay)
        
        # Prepare data for JSON files
        coco_data = {"images": [], "annotations": [], "categories": []}
        cvat_data = {"annotations": []}
        basic_list_data = []

        for idx, (name, bbox_coords, _) in enumerate(self.bounding_boxes):
            x1, y1, x2, y2 = [int(coord) for coord in bbox_coords]

            # COCO format
            coco_data["annotations"].append({
                "id": idx,
                "image_id": 1,  # Assuming single image
                "bbox": [x1, y1, x2 - x1, y2 - y1],  # COCO uses [x, y, width, height]
                "category_id": 1,  # Assuming single category
            })

            # CVAT format (simplified)
            cvat_data["annotations"].append({
                "id": idx,
                "label": name,
                "points": [x1, y1, x2, y2],
                "type": "rectangle",
            })

            # Basic list
            basic_list_data.append({"name": name, "bbox": [x1, y1, x2, y2]})

            # Draw bounding boxes on the overlay
            draw.rectangle([x1, y1, x2, y2], outline="red", fill=(0, 255, 0, 128))  # Semi-transparent green

        # Blend the overlay with the original image
        bbox_progress_img = Image.alpha_composite(inklabels_img.convert("RGBA"), bbox_overlay)
        bbox_progress_img = bbox_progress_img.convert("RGB")  # Convert back to RGB
        bbox_progress_img.save(os.path.join(output_dir, "bbox_progress.png"))

        # Save JSON files
        with open(os.path.join(output_dir, "coco_format.json"), 'w') as f:
            json.dump(coco_data, f, indent=4)

        with open(os.path.join(output_dir, "cvat_format.json"), 'w') as f:
            json.dump(cvat_data, f, indent=4)

        with open(os.path.join(output_dir, "basic_list_format.json"), 'w') as f:
            json.dump(basic_list_data, f, indent=4)

        total_operations = len(self.bounding_boxes) * (len(os.listdir(os.path.join(self.folder_path, 'layers'))) + 2)
        self.progress['maximum'] = total_operations
        current_operation = 0

        for name, bbox_coords, _ in self.bounding_boxes:
            folder_name = name if name else str(random.randint(1000, 9999))
            bbox_folder = os.path.join(output_dir, folder_name)
            os.makedirs(bbox_folder, exist_ok=True)

            # Create a 'layers' subfolder
            layers_folder = os.path.join(bbox_folder, 'layers')
            os.makedirs(layers_folder, exist_ok=True)

            x1, y1, x2, y2 = [int(coord) for coord in bbox_coords]
            inklabels_crop = inklabels_img.crop((x1, y1, x2, y2))
            mask_crop = mask_img.crop((x1, y1, x2, y2))

            inklabels_crop.save(os.path.join(bbox_folder, "inklabels.png"))
            mask_crop.save(os.path.join(bbox_folder, "mask.png"))

            # Process each layer TIF
            layers_path = os.path.join(self.folder_path, 'layers')
            for filename in os.listdir(layers_path):
                if filename.endswith('.tif'):
                    layer_img = Image.open(os.path.join(layers_path, filename))
                    layer_crop = layer_img.crop((x1, y1, x2, y2))
                    layer_crop.save(os.path.join(layers_folder, filename))

                    current_operation += 1
                    self.progress['value'] = current_operation
                    self.root.update_idletasks()

        self.progress['value'] = total_operations

# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
