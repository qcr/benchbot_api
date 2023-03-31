import matplotlib as mpl

mpl.use(
    'TkAgg'
)  # Default renderer Gtk3Agg had all sorts of stalling issues in matplotlib>=3.2

try:
    import matplotlib.pyplot as plt
except ImportError as e:
    import traceback
    import warnings
    warnings.formatwarning = (
        lambda msg, category, *args, **kwargs: '%s: %s\n' %
        (category.__name__, msg))
    warnings.warn(
        "Failed to import PyPlot from Matplotlib. Plotting functionality "
        "will error. Traceback is below:\n\n%s" % traceback.format_exc(),
        RuntimeWarning)
    plt = None

from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from scipy.spatial.transform import Rotation as Rot

SUPPORTED_OBSERVATIONS = [
    'image_rgb', 'image_depth', 'laser', 'poses', 'image_class',
    'image_instance'
]


def __plot_frame(ax, frame_name, frame_data):
    # NOTE currently assume that everything has parent frame 'map'
    L = 0.25
    # TODO BUG: map has no rotation aspect, handling it here but it should
    # have a rotation.
    origin = frame_data['translation_xyz']
    if 'rotation_rpy' in frame_data.keys():
        orientation = frame_data['rotation_rpy']
    else:
        orientation = [0, 0, 0]
    rot_obj = Rot.from_euler('xyz', orientation)
    x_vector = rot_obj.apply([1, 0, 0])
    y_vector = rot_obj.apply([0, 1, 0])
    z_vector = rot_obj.apply([0, 0, 1])
    origin = frame_data['translation_xyz']
    ax.quiver(origin[0],
              origin[1],
              origin[2],
              x_vector[0],
              x_vector[1],
              x_vector[2],
              length=L,
              normalize=True,
              color='r')
    ax.quiver(origin[0],
              origin[1],
              origin[2],
              y_vector[0],
              y_vector[1],
              y_vector[2],
              length=L,
              normalize=True,
              color='g')
    ax.quiver(origin[0],
              origin[1],
              origin[2],
              z_vector[0],
              z_vector[1],
              z_vector[2],
              length=L,
              normalize=True,
              color='b')
    ax.text(origin[0], origin[1], origin[2], frame_name)


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


def _create_diag_mask(mask_img, num_lines=7):
    diag_mask = np.zeros(mask_img.shape, bool)
    img_width = diag_mask.shape[1]
    # Note that minimum line width is 1
    line_width = max([np.min(diag_mask.shape) // num_lines, 1])
    # TODO Magic numbers in here ... don't do that
    bool_line = np.tile(
        np.append(np.ones(line_width, bool), np.zeros(line_width, bool)),
        (img_width * 2 // (line_width * 2)) + 2)
    for row_id in np.arange(diag_mask.shape[0]):
        start_idx = img_width - row_id % img_width
        # TODO there must be a better way to do this
        if (row_id // img_width) > 0 and (row_id // img_width) % 2 == 1:
            start_idx += line_width
        diag_mask[row_id, :] = bool_line[start_idx:(start_idx + img_width)]
    return np.logical_and(mask_img, diag_mask)


def _get_roi(img_mask):
    a = np.where(img_mask != 0)
    bbox = np.min(a[0]), np.max(a[0]) + 1, np.min(a[1]), np.max(a[1]) + 1
    return bbox


def _vis_rgb(ax, rgb_data):
    ax.clear()
    ax.imshow(rgb_data)
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    ax.set_title("image_rgb")


def _vis_depth(ax, depth_data):
    ax.clear()
    ax.imshow(depth_data,
              cmap="hot",
              clim=(np.amin(depth_data), np.amax(depth_data)))
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    ax.set_title("image_depth")


def _vis_class_segment(ax, segment_data):
    # Doing a little filtering to ignore unlabelled pixels
    ax.clear()
    class_segment_img = segment_data['class_segment_img']
    masked_class_segment = np.ma.masked_where(class_segment_img == 0,
                                              class_segment_img)
    # make background black
    ax.set_facecolor((0, 0, 0))
    num_class_colours = len(segment_data['class_ids']) + 1
    ax.imshow(masked_class_segment,
              cmap='gist_rainbow',
              clim=(1, num_class_colours),
              interpolation='nearest')
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    ax.set_title("image_class")


def _vis_inst_segment(ax, segment_data):
    # Setup instance segmentation image for visualization
    ax.clear()
    ax.set_facecolor((0, 0, 0))
    inst_segment_img = segment_data['instance_segment_img']

    # Add two images to the image that should not overlap
    # Images will contain class ID and instance ID adjacent with diagonals

    # Make diagonal pattern mask
    diagonal_mask_img = np.zeros(inst_segment_img.shape, bool)
    # Each instance will have its own diagonal mask proportional
    # to object size to help visualization
    for inst_id in np.unique(inst_segment_img):
        inst_mask_img = inst_segment_img == inst_id
        y0, y1, x0, x1 = _get_roi(inst_mask_img)
        inst_diag_mask = _create_diag_mask(inst_mask_img[y0:y1, x0:x1])
        diagonal_mask_img[y0:y1, x0:x1] = np.logical_or(
            diagonal_mask_img[y0:y1, x0:x1], inst_diag_mask)

    # First image is the class id with stripes
    class_segment_img = segment_data['class_segment_img']
    num_class_colours = len(segment_data['class_ids']) + 1
    masked_inst_class = np.ma.masked_where(
        np.logical_or(class_segment_img == 0,
                      np.logical_not(diagonal_mask_img)), class_segment_img)
    ax.imshow(masked_inst_class,
              cmap='gist_rainbow',
              clim=(1, num_class_colours),
              interpolation='nearest')

    # Second image is the instance id with stripes adjacent to
    # class id stripes
    # NOTE Instance IDs and corresponding colours will change
    # between images and depends on format CCIII (C class id, I inst id)
    inst_id_img = inst_segment_img % 1000
    masked_inst_segment = np.ma.masked_where(
        np.logical_or(inst_id_img == 0, diagonal_mask_img), inst_id_img)
    ax.imshow(masked_inst_segment,
              cmap='brg',
              clim=(1, max(np.amax(inst_id_img), 1)),
              interpolation='nearest')
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    ax.set_title("image_instance")


def _vis_laser(ax, laser_data):
    ax.clear()
    ax.plot(0, 0, c='r', marker=">")
    ax.scatter([x[0] * np.cos(x[1]) for x in laser_data['scans']],
               [x[0] * np.sin(x[1]) for x in laser_data['scans']],
               c='k',
               s=4,
               marker='s')
    ax.axis('equal')
    ax.set_title("laser (robot frame)")


def _vis_poses(ax, pose_data):
    ax.clear()
    __plot_frame(ax, 'map', {'translation_xyz': [0, 0, 0]})
    for k, v in pose_data.items():
        __plot_frame(ax, k, v)
    # ax.axis('equal') Unimplemented for 3d plots... wow...
    _set_axes_equal(ax)
    ax.set_title("poses (world frame)")


class ObservationVisualiser(object):

    def __init__(self,
                 vis_list=['image_rgb', 'image_depth', 'laser', 'poses']):
        self.fig = None
        self.axs = None
        self.vis_list = vis_list

    def update(self):
        # Performs a non-blocking update of the figure
        plt.draw()
        self.fig.canvas.start_event_loop(0.05)

    def visualise(self, observations, step_count=None):
        subplot_shape = (2, (len(self.vis_list) + 1) //
                         2) if len(self.vis_list) > 1 else (1, 1)
        if self.fig is None:
            plt.ion()
            self.fig, self.axs = plt.subplots(*subplot_shape)
            # Make sure that axis is always a 2D numpy array (reference purposes)
            if not isinstance(self.axs, np.ndarray):
                self.axs = np.array(self.axs).reshape(1, 1)
            if len(self.axs.shape) == 1:
                self.axs = self.axs[:, np.newaxis]

            # Set things up for poses (3D plot) if desired
            if 'poses' in self.vis_list:
                # NOTE currently assume poses can only exist once in the list
                poses_plt_num = int(
                    np.where(np.array(self.vis_list) == 'poses')[0])
                poses_subplt = (poses_plt_num % 2, poses_plt_num // 2)
                poses_plt_num_h = poses_subplt[0] * self.axs.shape[
                    1] + poses_subplt[1] + 1
                self.axs[poses_subplt].remove()
                self.axs[poses_subplt] = self.fig.add_subplot(
                    self.axs.shape[0],
                    self.axs.shape[1],
                    poses_plt_num_h,
                    projection='3d')

        self.fig.canvas.manager.set_window_title("Agent Observations" + (
            "" if step_count is None else " (step # %d)" % step_count))

        for plt_num, vis_type in enumerate(self.vis_list):
            subplt = (plt_num % 2, plt_num // 2)
            ax = self.axs[subplt]
            if vis_type == 'image_rgb':
                _vis_rgb(ax, observations['image_rgb'])
            elif vis_type == 'image_depth':
                _vis_depth(ax, observations['image_depth'])
            elif vis_type == 'image_class':
                _vis_class_segment(ax, observations['image_segment'])
            elif vis_type == 'image_instance':
                _vis_inst_segment(ax, observations['image_segment'])
            elif vis_type == 'laser':
                _vis_laser(ax, observations['laser'])
            elif vis_type == 'poses':
                _vis_poses(ax, observations['poses'])
            else:
                raise ValueError(
                    "\'{0}\' is not supported for visualization. Supported: {1}"
                    .format(vis_type, SUPPORTED_OBSERVATIONS))

        # Handle empty plot
        if len(self.vis_list) < self.axs.shape[0] * self.axs.shape[1]:
            # Currently assume there will only ever be one empty plot
            subplt = (self.axs.shape[0] - 1, self.axs.shape[1] - 1)
            self.axs[subplt].axis("off")

        self.update()
