from PIL import Image
from scipy import array
from matplotlib import pyplot as plt


#original = Image.open("edges.png")
#orig_array = array(original)

def find_contours(edges, nth=1):
    HEIGHT = len(edges)
    WIDTH = len(edges[0])

    viewed = set()
    starts = []

    def is_valid(x,y):
        return 0<=x<WIDTH and 0<=y<HEIGHT

    def get_neighbours(x,y):
        candidates = [(x-1,y-1), (x,y-1), (x+1,y-1),
                        (x-1,y),            (x+1,y),
                        (x-1,y+1), (x,y+1), (x+1,y+1)]
        result = [point for point in candidates if is_valid(point[0], point[1]) and edges[point[1]][point[0]]==255 and point not in viewed]
        return result

    def search(x,y):
        neighbours = get_neighbours(x,y)
        if len(neighbours)==0:
            next = []
        else:
            point = neighbours[0]
            viewed.add(point)
            next = search(point[0], point[1])
        for point in neighbours[1:]:
            viewed.add(point)
            path = [(point[0], point[1])]+search(point[0], point[1])
            path = array(path[::nth])
            final.append(path)
        return [(x,y)]+next

    for i in range(HEIGHT):     #y
        for j in range(WIDTH):  #x
            if edges[i][j] == 255 and len(get_neighbours(j,i))==1:
                starts.append((j,i))

    final = []
    for start in starts[0:]:
        viewed.add(start)
        points = [(start[0], start[1])]+search(start[0], start[1])
        points = array(points[::nth])
        if len(points)>=1:
            final.append(points)

    return final
"""
final = find_contours(orig_array)

print "Number of points:", len(array(final).flatten())

plt.subplot(1,2,1)
plt.imshow(original.convert('L'),cmap = 'gray')

plt.subplot(1,2,2, aspect='equal')
plt.gca().invert_yaxis()
for result in final:
    plt.plot( result[:,0], result[:,1], 'k-', linewidth=1)

plt.show()
"""