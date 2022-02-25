import io
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import matplotlib.path as path
import matplotlib.patches as patches


def drawPatch(ax, vertCodes, offx=0, offy=0, **kwargs):
    """
    For example:
    VertCodes = ( (x, y, c), (x, y, c), .. )    
    kwargs: facecolor='none', lw=1, edgecolor='r'
    """
    # cTable = path.Path.MOVETO, path.Path.LINETO, path.Path.CLOSEPOLY

    if len(vertCodes) == 0: return None
    vertices = [(offx + x, offy + y) for x, y, m in vertCodes]
    codes = [(path.Path.MOVETO if m == 0 else path.Path.LINETO) for x, y, m in vertCodes]

    codes[0] = path.Path.MOVETO
    layout = path.Path(vertices, codes)
    patch = patches.PathPatch(layout, **kwargs)
    ax.add_patch(patch)
    return patch

def annotate (ax, labels, xs, ys, color):
    for label, x, y in zip (labels, xs, ys):
        ax.annotate(label, xy=(x, y), xytext=(x, y), color=color)

def img2Bitmap(img, format="png"):
    """
    Given an image in a 2D array, returns a gray color image in a bitmap format, PNG or JPEG
    """
    outData = io.BytesIO()
    plt.imsave(outData, img, origin="lower", format=format, cmap="gray")
    outData.seek(0)
    return outData.read()
