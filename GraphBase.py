from src.backend.PluginManager.ActionBase import ActionBase

import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from PIL import Image
import io

class GraphBase(ActionBase):
    def __init__(self, deck_controller, page, coords):
        super().__init__(deck_controller=deck_controller, page=page, coords=coords)

        self.percentages: list[float] = []

    def set_percentages_lenght(self, length: int):
        if len(self.percentages) > length:
            self.percentages = self.percentages[-length:]
        elif len(self.percentages) < length:
            for _ in range(length - len(self.percentages)):
                self.percentages.insert(0, 0)
        
        return self.percentages
    
    def get_graph(self) -> Image:
        # Create a new figure with a transparent background
        fig = plt.figure(figsize=(6, 4))
        fig.patch.set_alpha(0)
        fig.patch.set_facecolor('none')

        # Set the FigureCanvas to the backend
        canvas = FigureCanvas(fig)

        # Plot the data with a transparent background
        ax = plt.Axes(fig, [0., 0., 1., 1.])
        ax.set_axis_off()
        fig.add_axes(ax)

        ax.plot(self.percentages, color='blue', linewidth=10)
        ax.fill_between(range(len(self.percentages)), self.percentages, color='skyblue', alpha=0.6)

        # Hide the spines
        for spine in ax.spines.values():
            spine.set_visible(False)

        # Turn off the axis and set margins to zero
        ax.margins(0)
        ax.axis('off')

        # Set the y-axis to range from 0 to 100
        ax.set_ylim(0, 100)

        # Draw the canvas and retrieve the buffer
        canvas.draw()
        buf = io.BytesIO()
        canvas.print_png(buf)

        # Convert buffer to a Pillow Image
        buf.seek(0)
        img = Image.open(buf)

        # The Pillow Image now has a transparent background
        # img.show()  # If you want to display the image
        # img.save('plot.png')  # If you want to save the image

        plt.close()  # Close the plot to free resources

        # Now 'img' is a Pillow Image object with a transparent background
        return img