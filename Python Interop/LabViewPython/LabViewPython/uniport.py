import cv2
from scipy import array
from scipy import uint8
from PIL import Image
from skimage import measure
import math
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button

mpl.rcParams['toolbar'] = 'None'
##################################################################
# Constants
##################################################################
rect = (200,120,440,360)	    # region of picture to crop
ncont = 30             		# number of selected contours
width = 15          		# of paper [cm]
L1 = 10.3           		# shoulder-elbow [cm]
L2 = 16.3   		        # elbow-wrist [cm]
offset = 12   		    	# shoulder to edge of sheet [cm]
angle_corr = 8.7   	    	# triangle wirst-elbow-marker [degrees]

while(True):
    ##################################################################
    # Taking image with webcam/loading from file
    ##################################################################
    use_cam = True

    if use_cam:
        box=(rect[0]+5, rect[1]+5, rect[2]-5,rect[3]-5) # contract region to avoid including border
        cap = cv2.VideoCapture(0)

        while True:
            ret,camimg = cap.read()
            cv2.rectangle(camimg,(rect[0],rect[1]),(rect[2],rect[3]),(0,255,0),1)
            cv2.imshow('video',camimg)

            key = cv2.waitKey(10)
            if key == 27:       # esc key
                break
            if ord('a')<=key<=ord('z') or key==ord(' '):   #press any key to take image
                camimg = Image.fromarray(uint8(camimg)).convert('L')
                camimg = camimg.crop(box)
                camimg=array(camimg)
                break

        cap.release()
        cv2.destroyAllWindows()

    else:
        camimg = Image.open("jake.jpg") # open colour image
        camimg = Image.fromarray(uint8(camimg)).convert('L') # convert image to monochrome - this works
        camimg=array(camimg)
        box=(0,0,len(camimg[0]), len(camimg))


    edges = camimg
    edges = cv2.Canny(edges,50,100)

    fig, ax = plt.subplots()
    fig.canvas.set_window_title('Adjustment')
    plt.subplots_adjust(bottom=0.25)

    plt.subplot(1,2,1),plt.imshow(camimg,cmap = 'gray')
    plt.title('Original'), plt.xticks([]), plt.yticks([])

    plt.subplot(1,2,2)
    edge_plot = plt.imshow(edges,cmap = 'gray')
    plt.title('Edges'), plt.xticks([]), plt.yticks([])

    axcolor = 'lightgoldenrodyellow'
    axupper = plt.axes([0.15, 0.15, 0.7, 0.03], axisbg=axcolor)
    upper = Slider(axupper, 'Upper', 0, 255, valinit=100)

    axlower = plt.axes([0.15, 0.1, 0.7, 0.03], axisbg=axcolor)
    lower = Slider(axlower, 'Lower', 0, 255, valinit=50)

    def update(val):
        global edges

        edges = camimg
        edges = cv2.Canny(edges,lower.val,upper.val)

        """
        contours = measure.find_contours(edges, 0.5)
        contours.sort(key=lambda x: -len(x))
        final = []
        for cont in contours[:ncont]:
            final.append(cont[::5]) #take every n-th point in contour
        contours = final[:]
        cont_ax.clear()
        for n, contour in enumerate(contours):
            cont_ax.plot(contour[:, 1], contour[:, 0],'k-', linewidth=1)
        plt.gca().invert_yaxis()
        cont_ax.set_title('Processed')
        cont_ax.set_xticks([])
        cont_ax.set_yticks([])
        """

        edge_plot.set_data(edges)
        fig.canvas.draw_idle()

    okax = plt.axes([0.8, 0.025, 0.1, 0.04])
    button = Button(okax, 'OK', color=axcolor, hovercolor='0.975')


    def reset(event):
        plt.close()

    button.on_clicked(reset)

    ###########################

    lower.on_changed(update)
    upper.on_changed(update)

    plt.show()

    edges = cv2.blur(edges,(3,3))
    contours = measure.find_contours(edges, 0.5)
    contours.sort(key=lambda x: -len(x))
    final = []

    for cont in contours[:ncont]:
        final.append(cont[::5]) #take every n-th point in contour

    contours = final[:]

    ##################################################################
    # Coordinate conversion, angle calculation and output to .CSV
    ##################################################################

    wp = box[2]-box[0]		# width of image (px)
    hp = box[3]-box[1]		# height of image (px)
    ratio = float(hp)/float(wp)	# ratio of image

    def to_motor_angles(x,y):
        # converts cartesian coordinates (x,y) in angle pairs (shoulder,elbow)
        r = (x**2+y**2)**0.5
        alpha = math.acos((L1**2+L2**2-r**2)/float(2*L1*L2))
        beta = math.atan(y/float(x))
        theta = beta + (math.pi if beta<0 else 0)
        sigma = math.asin(L2/float(r)*math.sin(alpha))
        delta = math.pi - theta + sigma
        return round(delta*180/math.pi,1), round(alpha*180/math.pi,1)-angle_corr      # shoulder, elbow

    def reverse_conversion(angle_shoulder,angle_elbow):
        rangle_shoulder = math.radians(angle_shoulder)
        rangle_elbow = math.radians(angle_elbow)
        reconvertx1 = -(L1*math.cos(rangle_shoulder))
        reconvertx2 = -(L2/math.cos(math.radians(angle_corr)))*math.cos(rangle_elbow+rangle_shoulder+math.radians(angle_corr)-math.pi)
        reconvertx = reconvertx1+reconvertx2
        reconverty1 = (L1*math.sin(rangle_shoulder))
        reconverty2 = (L2/math.cos(math.radians(angle_corr)))*math.sin(rangle_elbow+rangle_shoulder+math.radians(angle_corr)-math.pi)
        reconverty = reconverty1 + reconverty2
        return reconvertx,reconverty

    xpoints = []
    ypoints = []
    xre = []
    yre = []

    with open('output.csv', 'wb') as f:
        for cont in contours:
            count = 0
            for point in cont:
                try:
                    xreal = (width*ratio)*(point[0]/float(hp)-0.5)
                    yreal = width*point[1]/float(wp) + offset
                    delta,alpha = to_motor_angles(xreal,yreal)
                    f.write(','.join((str(delta),str(alpha)))+'\n')

                    xback,yback = reverse_conversion(delta,alpha)
                    xpoints.append(xreal)
                    ypoints.append(yreal)
                    xre.append(xback)
                    yre.append(yback)

                    print delta, alpha
                    count+=1
                except:     #unexpected math error
                    pass    #just don't include that point
            if count>0:
                f.write('-10,-10\n') #contour delimiter

    fig, ax = plt.subplots()
    fig.canvas.set_window_title('Outputs')
    plt.subplot(2,2,1), plt.imshow(camimg,cmap = 'gray')
    plt.title('Original'), plt.xticks([]), plt.yticks([])

    plt.subplot(2,2,2)
    plt.imshow(edges,cmap = 'gray')
    plt.title('Edges'), plt.xticks([]), plt.yticks([])

    cont_ax = plt.subplot(2,2,3)
    cont_ax.set_aspect('equal')
    plt.gca().invert_yaxis()

    for n, contour in enumerate(contours):
        cont_plot, = plt.plot(contour[:, 1], contour[:, 0],'k-', linewidth=1)

    plt.title('Contours'), plt.xticks([]), plt.yticks([])

    plt.subplot(2,2,4,aspect='equal'), plt.plot(xpoints, ypoints, 'r.',markersize=2), plt.plot(xre, yre, 'k.',markersize=2)
    plt.axis([-(offset+width)/2,(offset+width)/2,0,offset+width])
    plt.axhline(y=offset)
    plt.title('Expected vs. Real'), plt.xticks([]), plt.yticks([])

    plt.show()
