import matplotlib as mpl
mpl.use(
    'TkAgg'
)  # Default renderer Gtk3Agg had all sorts of stalling issues in matplotlib>=3.2

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from scipy.spatial.transform import Rotation as Rot


def _set_axes_radius(ax, origin, radius):
    ax.set_xlim3d([origin[0] - radius, origin[0] + radius])
    ax.set_ylim3d([origin[1] - radius, origin[1] + radius])
    ax.set_zlim3d([origin[2] - radius, origin[2] + radius])


def _set_axes_equal(ax):
    # Hacky function that creates an equal aspect ratio on 3D axes (as for
    # whatever reason, matplotlib's implementation has only managed to move
    # from silently failing to an unimplemented exception ...)
    limits = np.array([
        ax.get_xlim3d(),
        ax.get_ylim3d(),
        ax.get_zlim3d(),
    ])

    origin = np.mean(limits, axis=1)
    radius = 0.5 * np.max(np.abs(limits[:, 1] - limits[:, 0]))
    _set_axes_radius(ax, origin, radius)

def create_diag_mask(mask_img, num_lines=7):
    diag_mask = np.zeros(mask_img.shape, bool)
    img_width = diag_mask.shape[1]
    line_width = np.min(diag_mask.shape) // num_lines
    # TODO Magic numbers in here ... don't do that
    bool_line = np.tile(np.append(np.ones(line_width, bool),
                                  np.zeros(line_width, bool)),
                        (img_width*2 // (line_width*2)) + 2)
    for row_id in np.arange(diag_mask.shape[0]):
        start_idx = img_width - row_id % img_width
        # TODO there must be a better way to do this
        if (row_id // img_width) > 0 and (row_id // img_width) % 2 == 1:
            start_idx += line_width
        diag_mask[row_id,:] = bool_line[start_idx:(start_idx+img_width)]
    return np.logical_and(mask_img, diag_mask)

def get_roi(img_mask):
    a = np.where(img_mask != 0)
    bbox = np.min(a[0]), np.max(a[0])+1, np.min(a[1]), np.max(a[1])+1
    return bbox

class ObservationVisualiser(object):

    def __init__(self):
        self.fig = None
        self.axs = None

    def __plot_frame(self, frame_name, frame_data):
        # NOTE currently assume that everything has parent frame 'map'
        L = 0.5

        # TODO BUG: map has no rotation aspect, handling it here but it should
        # have a rotation.
        origin = frame_data['translation_xyz']
        if 'rotation_rpy' in frame_data.keys():
            orientation = frame_data['rotation_rpy']
        else:
            orientation = [0, 0, 0]
        rot_obj = Rot.from_euler('XYZ', orientation)
        x_vector = rot_obj.apply([1, 0, 0])
        y_vector = rot_obj.apply([0, 1, 0])
        z_vector = rot_obj.apply([0, 0, 1])
        origin = frame_data['translation_xyz']
        self.axs[1, 2].quiver(origin[0],
                              origin[1],
                              origin[2],
                              x_vector[0],
                              x_vector[1],
                              x_vector[2],
                              length=L,
                              normalize=True,
                              color='r')
        self.axs[1, 2].quiver(origin[0],
                              origin[1],
                              origin[2],
                              y_vector[0],
                              y_vector[1],
                              y_vector[2],
                              length=L,
                              normalize=True,
                              color='g')
        self.axs[1, 2].quiver(origin[0],
                              origin[1],
                              origin[2],
                              z_vector[0],
                              z_vector[1],
                              z_vector[2],
                              length=L,
                              normalize=True,
                              color='b')
        self.axs[1, 2].text(origin[0], origin[1], origin[2], frame_name)

    def update(self):
        # Performs a non-blocking update of the figure
        plt.draw()
        self.fig.canvas.start_event_loop(0.05)

    def visualise(self, observations, step_count=None):
        if self.fig is None:
            plt.ion()
            self.fig, self.axs = plt.subplots(2, 3)
            self.axs[1, 2].remove()
            self.axs[1, 2] = self.fig.add_subplot(2, 3, 6, projection='3d')

        self.fig.canvas.set_window_title("Agent Observations" + (
            "" if step_count is None else " (step # %d)" % step_count))

        self.axs[0, 0].clear()
        self.axs[0, 0].imshow(observations['image_rgb'])
        self.axs[0, 0].get_xaxis().set_visible(False)
        self.axs[0, 0].get_yaxis().set_visible(False)
        self.axs[0, 0].set_title("image_rgb")
        self.axs[1, 0].clear()
        self.axs[1, 0].imshow(observations['image_depth'],
                              cmap="hot",
                              clim=(np.amin(observations['image_depth']),
                                    np.amax(observations['image_depth'])))
        self.axs[1, 0].get_xaxis().set_visible(False)
        self.axs[1, 0].get_yaxis().set_visible(False)
        self.axs[1, 0].set_title("image_depth")
        # Doing a little filtering to ignore unlabelled pixels
        self.axs[0, 1].clear()
        class_segment_img = observations['image_segment']['class_segment_img']
        masked_class_segment = np.ma.masked_where(class_segment_img == 0, 
                                                  class_segment_img)
        # make background black
        self.axs[0, 1].set_facecolor((0,0,0))
        num_class_colours = len(observations['image_segment']['class_ids'])+1
        self.axs[0, 1].imshow(masked_class_segment,
                              cmap='gist_rainbow',
                              clim=(1,num_class_colours),
                              interpolation='nearest')
        self.axs[0, 1].get_xaxis().set_visible(False)
        self.axs[0, 1].get_yaxis().set_visible(False)
        self.axs[0, 1].set_title("image_class")
        # Setup instance segmentation image for visualization
        self.axs[1, 1].clear()
        self.axs[1, 1].set_facecolor((0,0,0))
        inst_segment_img = observations['image_segment']['instance_segment_img']
        # Add two images to the image that should not overlap
        # Images will contain class ID and instance ID adjacent with diagonals
        
        # Make diagonal pattern mask
        diagonal_mask_img = np.zeros(inst_segment_img.shape, bool)
        # Each instance will have its own diagonal mask to help visualization
        for inst_id in np.unique(inst_segment_img):
            inst_mask_img = inst_segment_img == inst_id
            y0, y1, x0, x1 = get_roi(inst_mask_img)
            inst_diag_mask = create_diag_mask(inst_mask_img[y0:y1, x0:x1])
            diagonal_mask_img[y0:y1, x0:x1] = np.logical_or(diagonal_mask_img[y0:y1, x0:x1],
                                                            inst_diag_mask)
        # diagonal_mask_img = create_diag_mask(diagonal_mask_img, 20)
        
        # First image is the class id with stripes
        masked_inst_class = np.ma.masked_where(np.logical_or(class_segment_img == 0,
                                                              np.logical_not(diagonal_mask_img)), 
                                               class_segment_img)
        self.axs[1, 1].imshow(masked_inst_class,
                              cmap='gist_rainbow',
                              clim=(1, num_class_colours),
                              interpolation='nearest')
        
        # Second image is the instance id with stripes
        # NOTE Instance IDs and corresponding colours will change
        # Between images
        inst_id_img = inst_segment_img % 1000
        masked_inst_segment = np.ma.masked_where(np.logical_or(inst_id_img == 0, 
                                                               diagonal_mask_img), 
                                                 inst_id_img)
        self.axs[1, 1].imshow(masked_inst_segment,
                              cmap='brg',
                              clim=(1, np.amax(inst_id_img),),
                              interpolation='nearest')
        self.axs[1, 1].get_xaxis().set_visible(False)
        self.axs[1, 1].get_yaxis().set_visible(False)
        self.axs[1, 1].set_title("image_instance")
        self.axs[0, 2].clear()
        self.axs[0, 2].plot(0, 0, c='r', marker=">")
        self.axs[0, 2].scatter(
            [x[0] * np.cos(x[1]) for x in observations['laser']['scans']],
            [x[0] * np.sin(x[1]) for x in observations['laser']['scans']],
            c='k',
            s=4,
            marker='s')
        self.axs[0, 2].axis('equal')
        self.axs[0, 2].set_title("laser (robot frame)")
        self.axs[1, 2].clear()
        self.__plot_frame('map', {'translation_xyz': [0, 0, 0]})
        for k, v in observations['poses'].items():
            self.__plot_frame(k, v)
        # self.axs[1, 1].axis('equal') Unimplemented for 3d plots... wow...
        _set_axes_equal(self.axs[1, 2])
        self.axs[1, 2].set_title("poses (world frame)")

        self.update()
