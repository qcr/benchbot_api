import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np


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


class ObservationVisualiser(object):

    def __init__(self):
        self.fig = None
        self.axs = None

    def __plot_frame(self, frame_name, frame_data):
        L = 1.0
        origin = frame_data['translation_xyz']
        self.axs[1, 1].quiver(origin[0],
                              origin[1],
                              origin[2],
                              1,
                              0,
                              0,
                              length=L,
                              normalize=True,
                              color='r')
        self.axs[1, 1].quiver(origin[0],
                              origin[1],
                              origin[2],
                              0,
                              1,
                              0,
                              length=L,
                              normalize=True,
                              color='g')
        self.axs[1, 1].quiver(origin[0],
                              origin[1],
                              origin[2],
                              0,
                              0,
                              1,
                              length=L,
                              normalize=True,
                              color='b')
        self.axs[1, 1].text(origin[0], origin[1], origin[2], frame_name)

    def update(self):
        # Performas a non-blocking update of the figure
        plt.draw()
        self.fig.canvas.start_event_loop(0.0001)

    def visualise(self, observations):
        if self.fig is None:
            plt.ion()
            self.fig, self.axs = plt.subplots(2, 2)
            self.axs[1, 1].remove()
            self.axs[1, 1] = self.fig.add_subplot(2, 2, 4, projection='3d')
            self.fig.canvas.set_window_title("Agent Observations")
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
        self.axs[0, 1].clear()
        self.axs[0, 1].plot(0, 0, c='r', marker=">")
        self.axs[0, 1].scatter(
            [x[0] * np.cos(x[1]) for x in observations['laser']['scans']],
            [x[0] * np.sin(x[1]) for x in observations['laser']['scans']],
            c='k',
            s=4,
            marker='s')
        self.axs[0, 1].axis('equal')
        self.axs[0, 1].set_title("laser (robot frame)")
        self.axs[1, 1].clear()
        self.__plot_frame('map', {'translation_xyz': [0, 0, 0]})
        for k, v in observations['poses'].items():
            self.__plot_frame(k, v)
        # self.axs[1, 1].axis('equal') Unimplemented for 3d plots... wow...
        _set_axes_equal(self.axs[1, 1])
        self.axs[1, 1].set_title("poses (world frame)")
