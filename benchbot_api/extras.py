import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from .tools import _set_axes_equal


CLASS_TO_COLOR_MAP = {
    'bottle':       'aqua',
    'cup':          'sandybrown',
    'knife':        'silver',
    'bowl':         'rosybrown',
    'wine glass':   'red',
    'fork':         'moccasin',
    'spoon':        'darkkhaki',
    'banana':       'yellow',
    'apple':        'green',
    'orange':       'orange',
    'cake':         'mistyrose',
    'potted plant': 'lawngreen',
    'mouse':        'gray',
    'keyboard':     'black',
    'laptop':       'firebrick',
    'cell phone':   'darkgreen',
    'book':         'saddlebrown',
    'clock':        'seagreen',
    'chair':        'lightseagreen',
    'table':        'darkcyan',
    'couch':        'deepskyblue',
    'bed':          'royalblue',
    'toilet':       'navy',
    'tv':           'blue',
    'microwave':    'mediumpurple',
    'toaster':      'darkorchid',
    'refrigerator': 'fuchsia',
    'oven':         'deeppink',
    'sink':         'crimson',
    'person':       'lightpink'
}


def get_bbox3d(extent, centroid):
    """ Calculate 3D bounding box corners from its parameterization.
    Input:
        extent: (length, width, height)
        centroid: (x, y, z)
    Output:
        corners3d:  3D box corners
    """

    l, w, h = extent

    corners3d = 0.5 * np.array([
        [-l, -l,  l,  l, -l, -l,  l, l],
        [ w, -w, -w,  w,  w, -w, -w, w],
        [-h, -h, -h, -h,  h,  h,  h, h],
    ])

    corners3d[0, :] = corners3d[0, :] + centroid[0]
    corners3d[1, :] = corners3d[1, :] + centroid[1]
    corners3d[2, :] = corners3d[2, :] + centroid[2]

    return corners3d.T


def vis_bbox3d(ax, bbox3d, facecolor, edgecolor, label):
    """ Visualise 3D bounding box.
    Input:
        ax: matplotlib axes 3D
        facecolor: bounding box facecolor
        edgecolor: bounding box edgecolor
        label: bounding box object class
    """
    # Cuboid sides
    surf_verts = [
        [bbox3d[0], bbox3d[1], bbox3d[2], bbox3d[3]],
        [bbox3d[4], bbox3d[5], bbox3d[6], bbox3d[7]],
        [bbox3d[0], bbox3d[1], bbox3d[5], bbox3d[4]],
        [bbox3d[2], bbox3d[3], bbox3d[7], bbox3d[6]],
        [bbox3d[1], bbox3d[2], bbox3d[6], bbox3d[5]],
        [bbox3d[4], bbox3d[7], bbox3d[3], bbox3d[0]]
    ]

    cuboid = Poly3DCollection(
        surf_verts,
        facecolors=facecolor,
        linewidths=1,
        edgecolors=edgecolor,
        alpha=.25,
        label=label
    )
    # Fix: 'Poly3DCollection' object has no attribute '_edgecolors2d'
    cuboid._facecolors2d = cuboid._facecolor3d
    cuboid._edgecolors2d = cuboid._edgecolor3d

    ax.add_collection3d(cuboid)
    ax.scatter3D(bbox3d[:, 0], bbox3d[:, 1], bbox3d[:, 2], s=1, color=edgecolor)


def vis_semantic_map3d(ax, scene_objects, class_to_color_map, edgecolor):
    for obj in scene_objects:
        label = obj['class']
        facecolor = class_to_color_map[label]
        bbox3d = get_bbox3d(obj['extent'], obj['centroid'])

        vis_bbox3d(ax, bbox3d, facecolor, edgecolor, label)

    _set_axes_equal(ax)
