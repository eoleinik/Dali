import cv2
from scipy import array
from scipy import uint8
import numpy as np
from PIL import Image
#from skimage.measure import find_contours
import math
from matplotlib import rcParams
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from alt_contour import find_contours

rcParams['toolbar'] = 'None'
##################################################################
# Constants
##################################################################
rect = (450,50,850,650)	    # region of picture to crop
#rect = (160 ,10, 480, 470)      # in windows virtual machine
ncont = 30
width = 15          		# of paper [cm]
L1 = 10.3           		# shoulder-elbow [cm]
L2 = 13.3   		        # elbow-wrist [cm] was: 16.3
offset = 8   		    	# shoulder to edge of sheet [cm]
angle_corr = 8.7   	    	# triangle wirst-elbow-marker [degrees]

##################################################################
# Taking image with webcam/loading from file
##################################################################
while True:
#for i in range(1):

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
                exit()
            if ord('a')<=key<=ord('z') or key==ord(' '):   #press any key to take image
                camimg = Image.fromarray(uint8(camimg)).convert('L')
                print camimg
                camimg = camimg.crop(box)
                camimg=array(camimg)
                break

        cap.release()
        cv2.destroyAllWindows()

    else:
        camimg = Image.open("jakie.jpg") # open colour image
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

    contours = find_contours(edges,5)
    contours.sort(key=lambda x: -len(x))

    i=0
    while len(contours[i])>1:
        i+=1
    final = contours[:i]

    def r(x1,y1,x2,y2):
        return ((x1-x2)**2+(y1-y2)**2)**0.5

    dist = 10
    num = 0
    while num<len(final):
        j = num+1
        while j<len(final):
            x1s,y1s,x1e,y1e = final[num][0][0], final[num][0][1], final[num][-1][0], final[num][-1][1]
            x2s,y2s,x2e,y2e = final[j][0][0], final[j][0][1], final[j][-1][0], final[j][-1][1]
            if r(x1s,y1s,x2s,y2s) <= dist:
                final[num] = np.concatenate((final[num][::-1],final[j]))
                del final[j]
            elif r(x1s,y1s,x2e,y2e) <= dist:
                final[num] = np.concatenate((final[j],final[num]))
                del final[j]
            elif r(x1e,y1e,x2s,y2s) <= dist:
                final[num] = np.concatenate((final[num],final[j]))
                del final[j]
            elif r(x1e,y1e,x2e,y2e) <= dist:
                final[num] = np.concatenate((final[num],final[j][::-1]))
                del final[j]
            j+=1
        num+=1

    contours = [cont for cont in final if len(cont)>10]
    contours.sort(key=lambda x: -len(x))


    print "found and sorted"
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
                    xreal = (width*ratio)*(point[1]/float(hp)-0.5)
                    yreal = width*point[0]/float(wp) + offset
                    delta,alpha = to_motor_angles(xreal,yreal)


                    xback,yback = reverse_conversion(delta,alpha)
                    xpoints.append(xreal)
                    ypoints.append(yreal)
                    xre.append(xback)
                    yre.append(yback)

                    if delta<195:
                        f.write(','.join((str(delta),str(alpha)))+'\n')
                        count+=1
                except:     #unexpected math error
                    pass    #just don't include that point
            if count>0:
                f.write('-10,-10\n') #contour delimiter

    print len(contours), sum([len(cont) for cont in contours])

    fig, ax = plt.subplots()
    fig.canvas.set_window_title('Outputs')
    plt.subplot(2,2,1),plt.imshow(camimg,cmap = 'gray')
    plt.title('Original'), plt.xticks([]), plt.yticks([])

    plt.subplot(2,2,2)
    plt.imshow(edges,cmap = 'gray')
    plt.title('Edges'), plt.xticks([]), plt.yticks([])

    cont_ax = plt.subplot(2,2,3)
    cont_ax.set_aspect('equal')
    plt.gca().invert_yaxis()

    for n, contour in enumerate(contours):
        cont_plot, = plt.plot(contour[:, 0], contour[:, 1],linewidth=1)

    plt.title('Contours'), plt.xticks([]), plt.yticks([])

    plt.subplot(2,2,4,aspect='equal')
    plt.gca().invert_yaxis()

    plt.plot(xpoints, ypoints, 'r.',markersize=2), plt.plot(xre, yre, 'k.',markersize=2)
    plt.axis([-(offset+width)/2,(offset+width)/2,0,offset+width])
    plt.axhline(y=offset)
    plt.title('Expected vs. Real'), plt.xticks([]), plt.yticks([])

    plt.show()